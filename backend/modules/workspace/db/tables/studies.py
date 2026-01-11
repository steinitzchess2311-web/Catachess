"""
Study and Chapter table definitions.

Studies are a special type of node that contain chapters.
Chapters store PGN content in R2 and metadata in the database.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from workspace.db.base import Base, TimestampMixin


class Study(Base, TimestampMixin):
    """
    Study metadata table.

    A study is a node that contains chapters (individual games).
    Each study has a limit of 64 chapters (Lichess compatibility).
    """

    __tablename__ = "studies"

    # Primary key (same as node_id in nodes table)
    id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("nodes.id", ondelete="CASCADE"),
        primary_key=True,
    )

    # Study-specific metadata
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Statistics
    chapter_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Visibility settings (mirrors node visibility)
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Tags for organization
    tags: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Indexes
    __table_args__ = (
        Index("ix_studies_is_public", "is_public"),
        Index("ix_studies_chapter_count", "chapter_count"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Study(id={self.id}, chapters={self.chapter_count})>"


class Chapter(Base, TimestampMixin):
    """
    Chapter metadata table.

    Each chapter represents one game (PGN) within a study.
    The actual PGN content is stored in R2, referenced by r2_key.
    """

    __tablename__ = "chapters"

    # Primary key
    id: Mapped[str] = mapped_column(String(64), primary_key=True)

    # Parent study
    study_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("studies.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Chapter metadata
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False)

    # PGN headers (cached from PGN for quick access)
    white: Mapped[str | None] = mapped_column(String(100), nullable=True)
    black: Mapped[str | None] = mapped_column(String(100), nullable=True)
    event: Mapped[str | None] = mapped_column(String(200), nullable=True)
    date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    result: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # R2 storage reference
    r2_key: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)

    # Integrity checking
    pgn_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    pgn_size: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # R2 metadata
    r2_etag: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Indexes
    __table_args__ = (
        Index("ix_chapters_study_id", "study_id"),
        Index("ix_chapters_study_order", "study_id", "order"),
        Index("ix_chapters_r2_key", "r2_key"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Chapter(id={self.id}, title={self.title})>"
