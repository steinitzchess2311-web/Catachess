"""
Group model
===========
A named group chat channel.

'name' is nullable — when null the display name is computed at query time
from the members list (e.g. "Alice, Bob, Charlie").
'last_message_at' is updated every time a message is sent and drives
the sort order in the sidebar.
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from modules.catchat.db.session import Base


class Group(Base):
    __tablename__ = "catchat_groups"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    last_message_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    # Optional structured metadata for categorisation (e.g. classroom source).
    # Example: {"source": "classroom", "classroom_id": "...", "classroom_name": "..."}
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=None)
