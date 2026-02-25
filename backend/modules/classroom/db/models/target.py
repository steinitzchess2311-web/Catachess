"""
AssignmentTarget model
======================
Controls which students see a given assignment.

  target_type='all'  → one row with username=NULL  → entire classroom
  target_type='user' → one row per username         → specific students

Query pattern — "is this assignment visible to student X?":
  SELECT 1 FROM assignment_targets
  WHERE assignment_id = :aid
    AND (target_type = 'all' OR (target_type = 'user' AND username = :username))
  LIMIT 1
"""
import uuid
from typing import Optional

from sqlalchemy import String, UniqueConstraint, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from modules.classroom.db.session import Base


class AssignmentTarget(Base):
    __tablename__ = "assignment_targets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    assignment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assignments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_type: Mapped[str] = mapped_column(String(10), nullable=False)
    # 'all' | 'user'
    username: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    # NULL when target_type='all'

    __table_args__ = (
        UniqueConstraint("assignment_id", "username", name="uq_assignment_target"),
    )
