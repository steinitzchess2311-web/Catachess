"""
Classroom model
===============
One row per classroom.

Soft-delete strategy:
  archived_at  — classroom is archived (recoverable, students can still view history)
  deleted_at   — classroom is permanently deleted (owner action, irreversible)

catchat_group_id is written after the catachat group is successfully created.
It may be NULL if catachat sync failed on creation.
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from modules.classroom.db.session import Base


class Classroom(Base):
    __tablename__ = "classrooms"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    owner: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Invite system
    invite_code: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, unique=True
    )
    invite_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )

    # Catachat linkage — written after group creation, NULL if sync failed
    catchat_group_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    # Workspace linkage — the shared folder node created in teacher's workspace
    # NULL if workspace sync failed or not yet synced
    workspace_folder_id: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    archived_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
