"""
Discussion thread table.
"""

from enum import Enum

from sqlalchemy import Boolean, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from workspace.db.base import Base, TimestampMixin


class ThreadType(str, Enum):
    """Discussion thread types."""

    QUESTION = "question"
    SUGGESTION = "suggestion"
    NOTE = "note"


class DiscussionThread(Base, TimestampMixin):
    """Discussion thread for a workspace target."""

    __tablename__ = "discussions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    target_id: Mapped[str] = mapped_column(String(64), nullable=False)
    target_type: Mapped[str] = mapped_column(String(32), nullable=False)
    author_id: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    thread_type: Mapped[ThreadType] = mapped_column(String(20), nullable=False)
    pinned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    resolved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1
    )

    __table_args__ = (
        Index("ix_discussions_target_id", "target_id"),
        Index("ix_discussions_target_type", "target_type"),
    )

    def __repr__(self) -> str:
        return f"<DiscussionThread(id={self.id}, target={self.target_id})>"
