"""
MaterialFork model
==================
Tracks per-student forks of teacher material chapters.

Each row links an assignment (category='material') to a student's personal
copy of the teacher's chapter in the student's workspace.
"""
import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from modules.classroom.db.session import Base


class MaterialFork(Base):
    __tablename__ = "material_forks"
    __table_args__ = (
        UniqueConstraint("assignment_id", "student_username", name="uq_material_fork_assignment_student"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    assignment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True,
    )
    student_username: Mapped[str] = mapped_column(String(50), nullable=False)
    fork_study_id: Mapped[str] = mapped_column(String(64), nullable=False)
    fork_chapter_id: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
