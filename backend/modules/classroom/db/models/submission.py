"""
Submission model
================
Records a student's attempt on an assignment.

attempt:  auto-incremented by the API layer per student per assignment.
          Never trust client-supplied attempt numbers.
status:   'in_progress' → student opened the task
          'submitted'   → student finished and submitted
          'graded'      → teacher has reviewed (future use)
score:    0.0–1.0 normalised; NULL for material (not graded).
detail:   JSONB — per-question breakdown, structure varies by assignment.type.
          Examples:
            tactics   → [{"puzzle_id": "...", "correct": true}, ...]
            trainer   → {"positions_seen": 10, "correct": 8}
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, SmallInteger, Float, UniqueConstraint, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from modules.classroom.db.session import Base


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    assignment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assignments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    username: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    attempt: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)

    status: Mapped[str] = mapped_column(String(15), nullable=False, default="in_progress")
    # 'in_progress' | 'submitted' | 'graded'

    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    # 0.0–1.0; NULL for material category

    detail: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    # per-attempt breakdown; structure depends on assignment.type

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    submitted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        UniqueConstraint("assignment_id", "username", "attempt", name="uq_submission"),
    )
