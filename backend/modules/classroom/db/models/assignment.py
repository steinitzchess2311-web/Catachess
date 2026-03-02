"""
Assignment model
================
Unified table for all three content types published by a teacher:

  category='material'   — reading material, not graded
  category='assignment' — graded task with optional deadline / attempts
  category='exam'       — graded, typically time-limited

type values by category:
  material:    'workspace' | 'upload'
  assignment:  'tactics' | 'opening' | 'trainer' | 'upload'
  exam:        'tactics' | 'opening'

source_type / source_ref:
  'study'   → source_ref = '{study_id}/{chapter_id}'
  'lichess' → source_ref = lichess puzzle set id
  'upload'  → source_ref = R2 object key

Soft-delete: deleted_at set by teacher; existing submissions are preserved.
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, Integer, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from modules.classroom.db.session import Base


class Assignment(Base):
    __tablename__ = "assignments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    classroom_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("classrooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_by: Mapped[str] = mapped_column(String(50), nullable=False)

    category: Mapped[str] = mapped_column(String(10), nullable=False)
    # 'material' | 'assignment' | 'exam'
    type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    # material:   'workspace' | 'upload'
    # assignment: 'tactics' | 'opening' | 'trainer' | 'upload'
    # exam:       'tactics' | 'opening'

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    source_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    # 'study' | 'lichess' | 'upload' | NULL
    source_ref: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    due_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    time_limit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # seconds; NULL = no time limit
    max_attempts: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # NULL = unlimited

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
