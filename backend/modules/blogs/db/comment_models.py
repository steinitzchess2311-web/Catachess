"""
Blog Comment Models

Two tables:
  blog_comments      — tree-structured comments (self-referencing parent_id)
  blog_comment_likes — one row per user-comment like pair
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from core.db.base import Base


class BlogComment(Base):
    """
    A single comment or nested reply on a blog article.

    Tree structure via self-referencing parent_id:
      parent_id = NULL  →  root comment
      parent_id = <id>  →  reply to that comment (unlimited depth)

    Soft-delete (is_deleted=True) keeps the node in the tree so child
    replies remain visible — shows "[已删除]" placeholder instead.
    """

    __tablename__ = "blog_comments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    article_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    # Parent comment — CASCADE so deleting a root removes the whole subtree
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("blog_comments.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    # Optional "quoting" another comment — SET NULL keeps the reply intact
    quote_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("blog_comments.id", ondelete="SET NULL"),
        nullable=True,
    )

    author_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    author_name: Mapped[str] = mapped_column(String(100), nullable=False)

    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Optimistic locking — edit must pass current version
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    edited: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # [{content, edited_at}] — last 10 entries kept
    edit_history: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    like_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<BlogComment(id={self.id}, article={self.article_id})>"


class BlogCommentLike(Base):
    """One row per (comment, user) — toggled via the like endpoint."""

    __tablename__ = "blog_comment_likes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    comment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("blog_comments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<BlogCommentLike(comment={self.comment_id}, user={self.user_id})>"
