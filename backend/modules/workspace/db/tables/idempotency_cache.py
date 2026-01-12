"""
Idempotency cache table definition.

Stores results of idempotent operations to prevent duplicate processing.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from workspace.db.base import Base


class IdempotencyCache(Base):
    """
    Idempotency cache table.

    Stores the result of idempotent operations keyed by the idempotency key.
    Entries automatically expire after a configured TTL.
    """

    __tablename__ = "idempotency_cache"

    # Idempotency key (from X-Idempotency-Key header or generated)
    key: Mapped[str] = mapped_column(String(255), primary_key=True)

    # Cached result (response data)
    result: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<IdempotencyCache(key={self.key}, expires_at={self.expires_at})>"
