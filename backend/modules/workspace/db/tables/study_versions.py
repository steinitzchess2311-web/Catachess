"""Study versions table definition."""
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from workspace.db.base import Base, TimestampMixin


class StudyVersionTable(Base, TimestampMixin):
    """
    Study version table.

    Tracks version history for studies with snapshots.
    """

    __tablename__ = "study_versions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    study_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    change_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    snapshot_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_rollback: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    created_by: Mapped[str] = mapped_column(String(64), nullable=False)

    # Relationship to snapshot (one-to-one)
    snapshot: Mapped["VersionSnapshotTable"] = relationship(
        "VersionSnapshotTable",
        back_populates="version",
        uselist=False,
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        # Unique constraint on study_id + version_number
        {"schema": None},
    )


class VersionSnapshotTable(Base):
    """
    Version snapshot table.

    Metadata for version snapshots. Actual content stored in R2.
    """

    __tablename__ = "version_snapshots"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    version_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("study_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    r2_key: Mapped[str] = mapped_column(String(512), nullable=False)
    size_bytes: Mapped[int | None] = mapped_column(nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    metadata: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    # Relationship back to version
    version: Mapped["StudyVersionTable"] = relationship(
        "StudyVersionTable",
        back_populates="snapshot"
    )
