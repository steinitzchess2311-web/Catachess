"""
Discussion reaction table.
"""

from sqlalchemy import Index, String
from sqlalchemy.orm import Mapped, mapped_column

from workspace.db.base import Base, TimestampMixin


class DiscussionReaction(Base, TimestampMixin):
    """Reaction to a thread or reply."""

    __tablename__ = "discussion_reactions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    target_id: Mapped[str] = mapped_column(String(64), nullable=False)
    target_type: Mapped[str] = mapped_column(String(16), nullable=False)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False)
    emoji: Mapped[str] = mapped_column(String(16), nullable=False)

    __table_args__ = (
        Index("ix_discussion_reactions_target", "target_id", "target_type"),
        Index("ix_discussion_reactions_user", "user_id"),
    )

    def __repr__(self) -> str:
        return f"<DiscussionReaction(id={self.id}, target={self.target_id})>"
