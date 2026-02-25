"""
Submission Pydantic schemas
"""
from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel, Field


# ── Requests ──────────────────────────────────────────────────────────────────

class SubmissionUpsert(BaseModel):
    """
    Used for both starting (in_progress) and finishing (submitted) a task.
    First call with status='in_progress' creates the record.
    Second call with status='submitted' closes it.
    """
    status: str = Field(..., pattern="^(in_progress|submitted)$")
    score: Optional[float] = Field(None, ge=0.0, le=1.0)
    detail: Optional[Any] = None   # JSONB — structure depends on assignment.type


# ── Responses ─────────────────────────────────────────────────────────────────

class SubmissionResponse(BaseModel):
    id: str
    assignment_id: str
    username: str
    attempt: int
    status: str
    score: Optional[float]
    detail: Optional[Any]
    started_at: datetime
    submitted_at: Optional[datetime]

    model_config = {"from_attributes": True}


class TodoItem(BaseModel):
    """
    Student-facing todo item — aggregated across all classrooms.
    urgency:
      'overdue'   — past due_date and not submitted
      'due_soon'  — due within 48 hours and not submitted
      'normal'    — has a due_date but not urgent, or no due_date
    """
    assignment_id: str
    title: str
    category: str
    classroom_id: str
    classroom_name: str
    due_date: Optional[datetime]
    urgency: str              # 'overdue' | 'due_soon' | 'normal'
    my_status: str            # 'not_started' | 'in_progress' | 'submitted'
