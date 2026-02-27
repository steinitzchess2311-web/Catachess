"""
Comment Service

Business logic for blog comments:
  - Create (with parent validation + article existence check)
  - Edit  (optimistic locking)
  - Soft-delete
  - Like toggle
  - Fetch flat list with is_liked enrichment
"""
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from modules.blogs.db.comment_models import BlogComment, BlogCommentLike
from modules.blogs.schemas.comment import CommentCreate, CommentEdit, CommentResponse


# ── Helpers ───────────────────────────────────────────────────────────────────

class CommentNotFoundError(Exception):
    pass

class OptimisticLockError(Exception):
    pass

class PermissionDeniedError(Exception):
    pass

class ArticleNotFoundError(Exception):
    pass


def _to_response(comment: BlogComment, is_liked: bool = False) -> CommentResponse:
    return CommentResponse(
        id=comment.id,
        article_id=comment.article_id,
        parent_id=comment.parent_id,
        quote_id=comment.quote_id,
        author_id=comment.author_id,
        author_name=comment.author_name,
        content=comment.content,
        is_deleted=comment.is_deleted,
        edited=comment.edited,
        like_count=comment.like_count,
        is_liked=is_liked,
        version=comment.version,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
    )


# ── Read ──────────────────────────────────────────────────────────────────────

def get_comments(
    db: Session,
    article_id: UUID,
    current_user_id: Optional[UUID] = None,
) -> list[CommentResponse]:
    """
    Return all non-deleted comments for an article as a flat list.
    Soft-deleted nodes are included (with is_deleted=True) so the
    frontend can render the "[已删除]" placeholder while keeping
    child replies visible.
    """
    comments = (
        db.query(BlogComment)
        .filter(BlogComment.article_id == article_id)
        .order_by(BlogComment.created_at.asc())
        .all()
    )

    liked_ids: set[str] = set()
    if current_user_id:
        rows = db.execute(
            text("""
                SELECT comment_id FROM blog_comment_likes
                WHERE comment_id IN (
                    SELECT id FROM blog_comments WHERE article_id = :aid
                ) AND user_id = :uid
            """),
            {"aid": str(article_id), "uid": str(current_user_id)},
        ).fetchall()
        liked_ids = {str(r[0]) for r in rows}

    return [_to_response(c, str(c.id) in liked_ids) for c in comments]


# ── Create ────────────────────────────────────────────────────────────────────

def create_comment(
    db: Session,
    article_id: UUID,
    payload: CommentCreate,
    author_id: UUID,
    author_name: str,
) -> CommentResponse:
    """
    Create a root comment or nested reply.
    Validates that parent_id (if given) belongs to the same article.
    """
    # Validate parent belongs to same article
    if payload.parent_id:
        parent = db.get(BlogComment, payload.parent_id)
        if not parent or parent.article_id != article_id or parent.is_deleted:
            raise CommentNotFoundError("Parent comment not found")

    # Validate quote belongs to same article
    if payload.quote_id:
        quoted = db.get(BlogComment, payload.quote_id)
        if not quoted or quoted.article_id != article_id:
            raise CommentNotFoundError("Quoted comment not found")

    comment = BlogComment(
        article_id=article_id,
        parent_id=payload.parent_id,
        quote_id=payload.quote_id,
        author_id=author_id,
        author_name=author_name,
        content=payload.content.strip(),
    )
    db.add(comment)

    # Increment article comment_count
    db.execute(
        text("UPDATE blog_articles SET comment_count = comment_count + 1 WHERE id = :id"),
        {"id": str(article_id)},
    )

    db.commit()
    db.refresh(comment)
    return _to_response(comment)


# ── Edit ──────────────────────────────────────────────────────────────────────

def edit_comment(
    db: Session,
    comment_id: UUID,
    payload: CommentEdit,
    actor_id: UUID,
    is_admin: bool = False,
) -> CommentResponse:
    """
    Edit a comment. Requires ownership (or admin).
    Uses optimistic locking — 409 if version mismatch.
    Stores old content in edit_history (max 10 entries).
    """
    comment = _get_live_comment(db, comment_id)

    if not is_admin and comment.author_id != actor_id:
        raise PermissionDeniedError("Not the comment author")

    if comment.version != payload.version:
        raise OptimisticLockError(
            f"Version conflict: expected {comment.version}, got {payload.version}"
        )

    entry = {
        "content": comment.content,
        "edited_at": datetime.now(timezone.utc).isoformat(),
    }
    comment.edit_history = (comment.edit_history + [entry])[-10:]
    comment.content = payload.content.strip()
    comment.edited = True
    comment.version += 1
    comment.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(comment)
    return _to_response(comment)


# ── Delete (soft) ─────────────────────────────────────────────────────────────

def delete_comment(
    db: Session,
    comment_id: UUID,
    actor_id: UUID,
    is_admin: bool = False,
) -> None:
    """
    Soft-delete a comment. Child replies remain visible.
    Only the author or an admin can delete.
    Decrements article comment_count.
    """
    comment = _get_live_comment(db, comment_id)

    if not is_admin and comment.author_id != actor_id:
        raise PermissionDeniedError("Not the comment author")

    comment.is_deleted = True
    comment.content = ""      # wipe content for privacy
    comment.updated_at = datetime.utcnow()

    db.execute(
        text("""
            UPDATE blog_articles
            SET comment_count = GREATEST(comment_count - 1, 0)
            WHERE id = :id
        """),
        {"id": str(comment.article_id)},
    )

    db.commit()


# ── Like toggle ───────────────────────────────────────────────────────────────

def toggle_like(
    db: Session,
    comment_id: UUID,
    user_id: UUID,
) -> tuple[bool, int]:
    """
    Toggle like on a comment. Returns (is_now_liked, new_like_count).
    Uses INSERT ... ON CONFLICT DO NOTHING for idempotency.
    """
    comment = _get_live_comment(db, comment_id)

    existing = db.execute(
        text("SELECT 1 FROM blog_comment_likes WHERE comment_id = :c AND user_id = :u"),
        {"c": str(comment_id), "u": str(user_id)},
    ).fetchone()

    if existing:
        db.execute(
            text("DELETE FROM blog_comment_likes WHERE comment_id = :c AND user_id = :u"),
            {"c": str(comment_id), "u": str(user_id)},
        )
        db.execute(
            text("UPDATE blog_comments SET like_count = GREATEST(like_count - 1, 0) WHERE id = :id"),
            {"id": str(comment_id)},
        )
        liked = False
    else:
        db.execute(
            text("INSERT INTO blog_comment_likes (comment_id, user_id) VALUES (:c, :u) ON CONFLICT DO NOTHING"),
            {"c": str(comment_id), "u": str(user_id)},
        )
        db.execute(
            text("UPDATE blog_comments SET like_count = like_count + 1 WHERE id = :id"),
            {"id": str(comment_id)},
        )
        liked = True

    db.commit()
    db.refresh(comment)
    return liked, comment.like_count


# ── Internal ──────────────────────────────────────────────────────────────────

def _get_live_comment(db: Session, comment_id: UUID) -> BlogComment:
    comment = db.get(BlogComment, comment_id)
    if not comment:
        raise CommentNotFoundError("Comment not found")
    if comment.is_deleted:
        raise CommentNotFoundError("Comment has been deleted")
    return comment
