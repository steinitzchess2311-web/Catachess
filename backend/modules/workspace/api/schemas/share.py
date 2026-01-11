"""
Share API schemas.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from workspace.domain.models.types import Permission


class ShareWithUser(BaseModel):
    """Schema for sharing with a user."""

    user_id: str
    permission: Permission
    inherit_to_children: bool = True


class RevokeShare(BaseModel):
    """Schema for revoking share."""

    user_id: str


class ChangeRole(BaseModel):
    """Schema for changing user role."""

    user_id: str
    new_permission: Permission


class CreateShareLink(BaseModel):
    """Schema for creating share link."""

    permission: Permission
    password: str | None = None
    expires_at: datetime | None = None


class ShareLinkResponse(BaseModel):
    """Schema for share link response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    object_id: str
    token: str
    permission: Permission
    expires_at: datetime | None
    created_by: str
    is_active: bool
    access_count: int
    created_at: datetime


class ACLResponse(BaseModel):
    """Schema for ACL response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    object_id: str
    user_id: str
    permission: Permission
    inherit_to_children: bool
    is_inherited: bool
    granted_by: str
    created_at: datetime


class SharedWithMeResponse(BaseModel):
    """Schema for shared-with-me response."""

    acl: ACLResponse
    node: Any  # NodeResponse (imported later to avoid circular)
