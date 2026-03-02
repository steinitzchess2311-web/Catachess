"""
Classroom Pydantic schemas
"""
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ── Requests ──────────────────────────────────────────────────────────────────

class ClassroomCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class ClassroomUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class InviteToggle(BaseModel):
    active: bool


class JoinByCode(BaseModel):
    invite_code: str = Field(..., min_length=1, max_length=20)


class BroadcastCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)


# ── Responses ─────────────────────────────────────────────────────────────────

class ClassroomResponse(BaseModel):
    id: str
    name: str
    owner: str
    invite_code: Optional[str]
    invite_active: bool
    catchat_group_id: Optional[str]
    workspace_folder_id: Optional[str]
    created_at: datetime
    archived_at: Optional[datetime]

    model_config = {"from_attributes": True}


class ClassroomListItem(BaseModel):
    """Compact representation used in list endpoints."""
    id: str
    name: str
    owner: str
    my_role: str          # 'owner' | 'teacher' | 'student'
    member_count: int
    archived_at: Optional[datetime]
    created_at: datetime
    workspace_folder_id: Optional[str] = None

    model_config = {"from_attributes": True}


class InviteResponse(BaseModel):
    invite_code: Optional[str]
    invite_active: bool


class ChatLinkResponse(BaseModel):
    catchat_group_id: Optional[str]


class BroadcastResponse(BaseModel):
    broadcast_id: str
    created_at: datetime


class BroadcastItem(BaseModel):
    broadcast_id: str
    sender_username: str
    content: str
    created_at: datetime


class ContactTeacherResponse(BaseModel):
    chat_type: str   # "conversation" | "group"
    chat_id: str
