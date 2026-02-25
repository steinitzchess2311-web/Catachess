"""
Member Pydantic schemas
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ── Requests ──────────────────────────────────────────────────────────────────

class MemberAdd(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    user_id: str = Field(..., description="UUID from auth service — passed through to catachat")
    role: str = Field("student", pattern="^(teacher|student)$")


class MemberRoleUpdate(BaseModel):
    role: str = Field(..., pattern="^(teacher|student)$")


# ── Responses ─────────────────────────────────────────────────────────────────

class MemberResponse(BaseModel):
    username: str
    role: str             # 'owner' | 'teacher' | 'student'
    invited_by: Optional[str]
    joined_at: datetime

    model_config = {"from_attributes": True}
