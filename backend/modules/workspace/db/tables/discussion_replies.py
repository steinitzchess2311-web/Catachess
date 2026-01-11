"""
Discussion reply table.
"""

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from workspace.db.base import Base, TimestampMixin


class DiscussionReply(Base, TimestampMixin):
    """Reply in a discussion thread."""

    __tablename__ = "discussion_replies"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    thread_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("discussions.id", ondelete="CASCADE"),
        nullable=False,
    )
    parent_reply_id: Mapped[str | None] = mapped_column(
        String(64),
        ForeignKey("discussion_replies.id", ondelete="CASCADE"),
        nullable=True,
    )
    quote_reply_id: Mapped[str | None] = mapped_column(
        String(64),
        ForeignKey("discussion_replies.id", ondelete="SET NULL"),
        nullable=True,
    )
    author_id: Mapped[str] = mapped_column(String(64), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    edited: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    edit_history: Mapped[list[dict]] = mapped_column(
        JSON, nullable=False, default=list
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    __table_args__ = (
        Index("ix_discussion_replies_thread_id", "thread_id"),
        Index("ix_discussion_replies_parent_id", "parent_reply_id"),
    )

    def __repr__(self) -> str:
        return f"<DiscussionReply(id={self.id}, thread={self.thread_id})>"
