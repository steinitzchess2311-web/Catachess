"""
SQLAlchemy base configuration and utilities.
"""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models.

    Provides common functionality and conventions.
    """

    pass


class TimestampMixin:
    """
    Mixin for created_at and updated_at timestamps.

    Automatically tracks creation and modification times.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class SoftDeleteMixin:
    """
    Mixin for soft delete functionality.

    Objects are marked as deleted rather than removed from database.
    """

    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    @property
    def is_deleted(self) -> bool:
        """Check if object is soft-deleted."""
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        """Mark object as deleted."""
        self.deleted_at = datetime.now(UTC)

    def restore(self) -> None:
        """Restore soft-deleted object."""
        self.deleted_at = None
