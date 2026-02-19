"""
Broadcast model
===============
Admin-to-all announcement messages.
Any authenticated user can read; only role='admin' can write.

sender_name is denormalised for display speed (no cross-DB join needed).
"""
import uuid
from datetime import datetime

from sqlalchemy import Text, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from modules.catchat.db.session import Base


class Broadcast(Base):
    __tablename__ = "catchat_broadcasts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    sender_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    sender_name: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )
