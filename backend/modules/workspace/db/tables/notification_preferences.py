from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from workspace.db.base import Base, TimestampMixin


class NotificationPreference(Base, TimestampMixin):
    __tablename__ = "notification_preferences"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True, unique=True)

    # Event-specific preferences (JSON: {event_type: {enabled: bool, channels: [str]}})
    preferences: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # Digest settings
    digest_frequency: Mapped[str] = mapped_column(
        String(32), nullable=False, default="instant"
    )  # instant, hourly, daily, weekly

    # Quiet hours (JSON: {enabled: bool, start_hour: int, end_hour: int})
    quiet_hours: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # Muted objects (JSON: [target_id])
    muted_objects: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    # Global notification enable/disable
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
