"""
Conversation model
==================
Represents a unique private channel between exactly two users.

Uniqueness: user1_id < user2_id (enforced in API layer via _sorted_pair).
This guarantees one row per pair regardless of who initiates.
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from modules.catchat.db.session import Base


class Conversation(Base):
    __tablename__ = "catchat_conversations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # user1_id is always < user2_id (UUID comparison) — enforced at write time
    user1_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    user2_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    # Updated every time a new message is sent — drives conversation list sort order
    last_message_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    __table_args__ = (
        UniqueConstraint("user1_id", "user2_id", name="uq_catchat_conv_pair"),
    )
