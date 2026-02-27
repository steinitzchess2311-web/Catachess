"""
Blog Comments API

Endpoints:
  GET    /api/blogs/articles/{article_id}/comments        — list (flat, auth-aware)
  POST   /api/blogs/articles/{article_id}/comments        — create (auth required)
  PUT    /api/blogs/comments/{comment_id}                  — edit (author/admin)
  DELETE /api/blogs/comments/{comment_id}                  — soft-delete (author/admin)
  POST   /api/blogs/comments/{comment_id}/like             — toggle like (auth required)
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from modules.blogs.auth import get_current_user, get_current_user_optional, get_blog_db
from modules.blogs.schemas.comment import CommentCreate, CommentEdit, CommentListResponse, CommentResponse
from modules.blogs.services import comment_service as svc

router = APIRouter(tags=["Blog Comments"])


# ── List ──────────────────────────────────────────────────────────────────────

@router.get("/articles/{article_id}/comments", response_model=CommentListResponse)
def list_comments(
    article_id: UUID,
    db: Session = Depends(get_blog_db),
    current_user=Depends(get_current_user_optional),
):
    """
    Return all comments for an article as a flat list.
    Frontend builds the tree from parent_id.
    is_liked is populated when the user is logged in.
    """
    user_id = current_user.id if current_user else None
    items = svc.get_comments(db, article_id, user_id)
    return CommentListResponse(items=items, total=len(items))


# ── Create ────────────────────────────────────────────────────────────────────

@router.post("/articles/{article_id}/comments", response_model=CommentResponse, status_code=201)
def create_comment(
    article_id: UUID,
    payload: CommentCreate,
    db: Session = Depends(get_blog_db),
    current_user=Depends(get_current_user),
):
    """Create a root comment or nested reply. Requires login."""
    try:
        author_name = current_user.username or current_user.identifier or "用户"
        return svc.create_comment(
            db, article_id, payload,
            author_id=current_user.id,
            author_name=author_name,
        )
    except svc.CommentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ── Edit ──────────────────────────────────────────────────────────────────────

@router.put("/comments/{comment_id}", response_model=CommentResponse)
def edit_comment(
    comment_id: UUID,
    payload: CommentEdit,
    db: Session = Depends(get_blog_db),
    current_user=Depends(get_current_user),
):
    """Edit a comment. Must be the author. Passes version for optimistic locking."""
    is_admin = getattr(current_user, "role", "") == "admin"
    try:
        return svc.edit_comment(db, comment_id, payload, current_user.id, is_admin)
    except svc.CommentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except svc.OptimisticLockError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except svc.PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))


# ── Delete ────────────────────────────────────────────────────────────────────

@router.delete("/comments/{comment_id}", status_code=204)
def delete_comment(
    comment_id: UUID,
    db: Session = Depends(get_blog_db),
    current_user=Depends(get_current_user),
):
    """Soft-delete a comment (keeps tree structure intact)."""
    is_admin = getattr(current_user, "role", "") == "admin"
    try:
        svc.delete_comment(db, comment_id, current_user.id, is_admin)
    except svc.CommentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except svc.PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))


# ── Like ──────────────────────────────────────────────────────────────────────

@router.post("/comments/{comment_id}/like")
def like_comment(
    comment_id: UUID,
    db: Session = Depends(get_blog_db),
    current_user=Depends(get_current_user),
):
    """Toggle like on a comment. Returns {liked, like_count}."""
    try:
        liked, like_count = svc.toggle_like(db, comment_id, current_user.id)
        return {"liked": liked, "like_count": like_count}
    except svc.CommentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
