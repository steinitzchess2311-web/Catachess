"""
Verification Code ORM model for email/phone verification
"""
import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.db.base import Base


class VerificationCode(Base):
    __tablename__ = "verification_codes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    code_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    purpose: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="signup",
    )  # "signup", "password_reset", etc.

    expires_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    consumed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    __table_args__ = (
        # Ensure only one active (non-consumed, non-expired) code per user/purpose
        Index(
            "idx_verification_active",
            "user_id",
            "purpose",
            "consumed_at",
            unique=False,
        ),
    )
