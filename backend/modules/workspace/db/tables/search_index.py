"""
Search index table.
"""

from sqlalchemy import Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from workspace.db.base import Base, TimestampMixin


class SearchIndex(Base, TimestampMixin):
    """Simple search index entry."""

    __tablename__ = "search_index"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    target_id: Mapped[str] = mapped_column(String(64), nullable=False)
    target_type: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        Index("ix_search_index_target", "target_id", "target_type"),
    )
