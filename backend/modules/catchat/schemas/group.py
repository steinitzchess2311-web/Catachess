from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ── Member ───────────────────────────────────────────────────────────────────

class GroupMemberInfo(BaseModel):
    user_id: str
    username: str
    role: str   # 'owner' | 'admin' | 'member'
    joined_at: datetime

    model_config = {"from_attributes": True}


class GroupMemberInput(BaseModel):
    """A user to include when creating a group (id + username already known from search)."""
    user_id: str
    username: str


class MemberAdd(BaseModel):
    """Add an existing user to a group (admin+ only)."""
    user_id: str
    username: str


class MemberRoleUpdate(BaseModel):
    """Change a member's role (owner only). Valid values: 'admin', 'member'."""
    role: str


# ── Group ────────────────────────────────────────────────────────────────────

class GroupCreate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    members: list[GroupMemberInput]  # [{user_id, username}, ...]


class GroupUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class GroupResponse(BaseModel):
    id: str
    name: str           # stored name, or auto-generated from members
    created_by: str
    created_at: datetime
    last_message_at: datetime
    members: list[GroupMemberInfo] = []
    meta: Optional[dict] = None

    model_config = {"from_attributes": True}


# ── Group messages ────────────────────────────────────────────────────────────

class GroupMessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)


class GroupMessageResponse(BaseModel):
    id: str
    group_id: str
    sender_id: str
    sender_name: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}
