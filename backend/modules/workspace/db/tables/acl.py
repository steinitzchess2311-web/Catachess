"""
ACL (Access Control List) table definitions.

Manages permissions and sharing for workspace objects.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, synonym

from workspace.db.base import Base, TimestampMixin
from workspace.domain.models.types import Permission


class ACL(Base, TimestampMixin):
    """
    Access Control List entry.

    Maps (object_id, user_id) -> permission level.
    Supports permission inheritance from parent nodes.
    """

    __tablename__ = "acl"

    # Primary key
    id: Mapped[str] = mapped_column(String(64), primary_key=True)

    # Object being shared (node_id)
    object_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Compatibility alias for older code/tests
    node_id = synonym("object_id")

    # User being granted access
    user_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    # Permission level
    permission: Mapped[Permission] = mapped_column(String(20), nullable=False)
    # Compatibility alias for older code/tests
    role = synonym("permission")

    # Inheritance settings
    # If True, this permission applies to all children of this object
    inherit_to_children: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # If True, this is an inherited permission (from parent)
    is_inherited: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # If inherited, which object it was inherited from
    inherited_from: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Granted by (for audit)
    granted_by: Mapped[str] = mapped_column(String(64), nullable=False)

    # Indexes and constraints
    __table_args__ = (
        # Unique constraint: one permission per (object, user) pair
        UniqueConstraint("object_id", "user_id", name="uq_acl_object_user"),
        # Fast user permission lookups
        Index("ix_acl_user_object", "user_id", "object_id"),
        # Fast object permission lookups
        Index("ix_acl_object_permission", "object_id", "permission"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<ACL(object={self.object_id}, user={self.user_id}, "
            f"permission={self.permission})>"
        )


class ShareLink(Base, TimestampMixin):
    """
    Shareable link for objects.

    Allows access via token rather than explicit user grant.
    Links can have passwords and expiry times.
    """

    __tablename__ = "share_links"

    # Primary key
    id: Mapped[str] = mapped_column(String(64), primary_key=True)

    # Object being shared
    object_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Token (public identifier in URL)
    token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)

    # Permission granted via this link
    permission: Mapped[Permission] = mapped_column(String(20), nullable=False)

    # Optional password (hashed)
    password_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # Optional expiry
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Creator
    created_by: Mapped[str] = mapped_column(String(64), nullable=False)

    # Whether link is active
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Usage tracking
    access_count: Mapped[int] = mapped_column(default=0, nullable=False)
    last_accessed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Indexes
    __table_args__ = (
        # Fast token lookup
        Index("ix_share_links_token_active", "token", "is_active"),
        # Fast expiry queries (for cleanup)
        Index("ix_share_links_expires_at", "expires_at"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<ShareLink(object={self.object_id}, token={self.token[:8]}...)>"

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

    def increment_access_count(self) -> None:
        """Increment access count and update last accessed time."""
        self.access_count += 1
        self.last_accessed_at = datetime.utcnow()
