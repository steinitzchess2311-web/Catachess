"""
ACL domain model.

Represents access control and sharing.
"""

from dataclasses import dataclass
from datetime import datetime

from workspace.domain.models.types import Permission


@dataclass
class ACLModel:
    """
    Domain model for ACL entry.

    Represents a permission grant for a user on an object.
    """

    id: str
    object_id: str
    user_id: str
    permission: Permission
    inherit_to_children: bool
    is_inherited: bool
    inherited_from: str | None
    granted_by: str
    created_at: datetime
    updated_at: datetime

    def can_read(self) -> bool:
        """Check if permission allows reading."""
        return Permission.can_read(self.permission)

    def can_write(self) -> bool:
        """Check if permission allows writing."""
        return Permission.can_write(self.permission)

    def can_manage_acl(self) -> bool:
        """Check if permission allows managing ACL."""
        return Permission.can_manage_acl(self.permission)

    def can_delete(self) -> bool:
        """Check if permission allows deletion."""
        return Permission.can_delete(self.permission)


@dataclass
class ShareLinkModel:
    """
    Domain model for share link.

    Represents a shareable link for an object.
    """

    id: str
    object_id: str
    token: str
    permission: Permission
    password_hash: str | None
    expires_at: datetime | None
    created_by: str
    is_active: bool
    access_count: int
    last_accessed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @property
    def is_expired(self) -> bool:
        """Check if link has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if link is valid (active and not expired)."""
        return self.is_active and not self.is_expired


@dataclass
class ShareCommand:
    """Command to share an object with a user."""

    object_id: str
    user_id: str
    permission: Permission
    granted_by: str
    inherit_to_children: bool = True


@dataclass
class RevokeShareCommand:
    """Command to revoke a share."""

    object_id: str
    user_id: str


@dataclass
class ChangeRoleCommand:
    """Command to change user's permission level."""

    object_id: str
    user_id: str
    new_permission: Permission


@dataclass
class CreateShareLinkCommand:
    """Command to create a share link."""

    object_id: str
    permission: Permission
    created_by: str
    password: str | None = None
    expires_at: datetime | None = None


@dataclass
class RevokeShareLinkCommand:
    """Command to revoke a share link."""

    link_id: str
