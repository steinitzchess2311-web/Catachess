"""
Presence sessions table definition.

Tracks active user sessions for real-time collaboration.
"""

from datetime import datetime, UTC
from sqlalchemy import String, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from workspace.db.base import Base, TimestampMixin


class PresenceSessionTable(Base, TimestampMixin):
    """
    Presence session table.

    Tracks user presence in studies for real-time collaboration.
    """

    __tablename__ = "presence_sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    study_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    chapter_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    move_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, server_default="active")
    last_heartbeat: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True
    )

    __table_args__ = (
        Index("ix_presence_sessions_user_study", "user_id", "study_id", unique=True),
    )
