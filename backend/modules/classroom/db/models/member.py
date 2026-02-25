"""
ClassroomMember model
=====================
Per-classroom role system. A user can be teacher in one classroom
and student in another — identity is determined here, not on the account.

Roles:
  'teacher' — can manage classroom, publish assignments, view all submissions
  'student' — can view assignments, submit work

The classroom owner (classrooms.owner) is separate and not stored here.
All three (owner, teacher, student) are valid API actors.

Soft-delete: removed_at is set instead of deleting rows.
Re-inviting the same user: update removed_at back to NULL.
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, UniqueConstraint, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from modules.classroom.db.session import Base


class ClassroomMember(Base):
    __tablename__ = "classroom_members"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    classroom_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("classrooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    role: Mapped[str] = mapped_column(
        String(10), nullable=False
    )  # 'teacher' | 'student'

    invited_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Workspace linkage — the student's subfolder node under the classroom folder
    # NULL if workspace sync failed or not yet synced
    workspace_folder_id: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    removed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        # One row per (classroom, user) — includes removed rows.
        # Re-invite = unset removed_at, not new row.
        UniqueConstraint("classroom_id", "username", name="uq_classroom_member"),
    )
