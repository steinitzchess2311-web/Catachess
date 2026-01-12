"""
User ORM model
"""
import uuid
from datetime import datetime

from sqlalchemy import String, Boolean, DateTime, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    identifier: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    identifier_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )  # "email" | "phone"

    username: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="student",
    )  # "student" | "teacher"

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # SECURITY FIX: Added is_verified field to track email/phone verification status
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # Chess profile fields (optional, set by users in settings after signup)
    # Online chess platform usernames
    lichess_username: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    chesscom_username: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    # Chess ratings from different organizations
    fide_rating: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    cfc_rating: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )  # Chess Federation of Canada

    ecf_rating: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )  # English Chess Federation

    # Chess titles
    chinese_athlete_title: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    fide_title: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
    )  # GM, IM, FM, CM, WGM, WIM, WFM, WCM

    # Self introduction
    self_intro: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
