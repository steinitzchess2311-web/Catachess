"""
Assignment Pydantic schemas
"""
import uuid
from datetime import datetime
from typing import Optional, Literal, Union

from pydantic import BaseModel, Field, model_validator


# ── Target spec (used in create request) ──────────────────────────────────────

class TargetAll(BaseModel):
    type: Literal["all"]


class TargetUsers(BaseModel):
    type: Literal["users"]
    usernames: list[str] = Field(..., min_length=1)


TargetSpec = Union[TargetAll, TargetUsers]


# ── Requests ──────────────────────────────────────────────────────────────────

_VALID_TYPES = {
    "material":   {"workspace", "upload"},
    "assignment": {"tactics", "opening", "trainer", "upload"},
    "exam":       {"tactics", "opening"},
}

_VALID_SOURCE_TYPES = {"study", "lichess", "upload"}


class AssignmentCreate(BaseModel):
    category: str = Field(..., pattern="^(material|assignment|exam)$")
    type: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    source_type: Optional[str] = None
    source_ref: Optional[str] = Field(None, max_length=500)
    due_date: Optional[datetime] = None
    time_limit: Optional[int] = Field(None, gt=0, description="seconds")
    max_attempts: Optional[int] = Field(None, gt=0)
    targets: TargetSpec

    @model_validator(mode="after")
    def validate_type_for_category(self) -> "AssignmentCreate":
        # type is optional for material category; required for others
        if self.type is not None:
            allowed = _VALID_TYPES.get(self.category, set())
            if self.type not in allowed:
                raise ValueError(
                    f"type '{self.type}' is not valid for category '{self.category}'. "
                    f"Allowed: {sorted(allowed)}"
                )
        elif self.category != "material":
            allowed = _VALID_TYPES.get(self.category, set())
            raise ValueError(
                f"type is required for category '{self.category}'. "
                f"Allowed: {sorted(allowed)}"
            )
        if self.source_type and self.source_type not in _VALID_SOURCE_TYPES:
            raise ValueError(f"source_type must be one of {_VALID_SOURCE_TYPES}")
        return self


class AssignmentUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    time_limit: Optional[int] = Field(None, gt=0)
    max_attempts: Optional[int] = Field(None, gt=0)


# ── Responses ─────────────────────────────────────────────────────────────────

class AssignmentResponse(BaseModel):
    id: str
    classroom_id: str
    created_by: str
    category: str
    type: Optional[str]
    title: str
    description: Optional[str]
    source_type: Optional[str]
    source_ref: Optional[str]
    due_date: Optional[datetime]
    time_limit: Optional[int]
    max_attempts: Optional[int]
    created_at: datetime
    targets: TargetSpec

    model_config = {"from_attributes": True}


class AssignmentListItem(BaseModel):
    """Used in list endpoints — includes viewer-specific fields."""
    id: str
    title: str
    category: str
    type: Optional[str]
    due_date: Optional[datetime]
    created_at: datetime
    # Student view
    my_submission: Optional[dict] = None   # {status, score, attempt} | None
    # Teacher view
    submission_count: Optional[int] = None
    member_count: Optional[int] = None


class AssignmentStatsPerStudent(BaseModel):
    username: str
    status: Optional[str]
    score: Optional[float]
    attempt: Optional[int]
    submitted_at: Optional[datetime]


class AssignmentStats(BaseModel):
    assignment_id: str
    total_targets: int
    submitted: int
    in_progress: int
    not_started: int
    overdue: int
    avg_score: Optional[float]
    score_distribution: list[float]   # one entry per submitted student
    per_student: list[AssignmentStatsPerStudent]
