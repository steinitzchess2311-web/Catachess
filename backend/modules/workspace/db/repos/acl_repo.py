"""
ACL repository for permission management.
"""

from typing import Sequence

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from workspace.db.tables.acl import ACL, ShareLink
from workspace.domain.models.types import Permission


class ACLRepository:
    """
    Repository for ACL database operations.

    Handles permission grants and share links.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize repository.

        Args:
            session: Database session
        """
        self.session = session

    # === ACL Operations ===

    async def create_acl(self, acl: ACL) -> ACL:
        """Create a new ACL entry."""
        if not acl.granted_by:
            acl.granted_by = acl.user_id
        self.session.add(acl)
        await self.session.flush()
        return acl

    async def create(self, acl: ACL) -> ACL:
        """Compatibility alias for create_acl (used by tests)."""
        return await self.create_acl(acl)

    async def get_acl(self, object_id: str, user_id: str) -> ACL | None:
        """Get ACL entry for object and user."""
        stmt = select(ACL).where(
            and_(ACL.object_id == object_id, ACL.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_acls_for_object(self, object_id: str) -> Sequence[ACL]:
        """Get all ACL entries for an object."""
        stmt = select(ACL).where(ACL.object_id == object_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_acls_for_user(self, user_id: str) -> Sequence[ACL]:
        """Get all ACL entries for a user (objects shared with them)."""
        stmt = select(ACL).where(ACL.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_acls_with_nodes_for_user(self, user_id: str) -> Sequence[tuple[ACL, any]]:
        """
        Get all ACL entries with their associated nodes for a user.

        Uses a join to avoid N+1 query problem.

        Args:
            user_id: User ID

        Returns:
            List of (ACL, Node) tuples for non-deleted nodes
        """
        from workspace.db.tables.nodes import Node

        stmt = (
            select(ACL, Node)
            .join(Node, ACL.object_id == Node.id)
            .where(
                and_(
                    ACL.user_id == user_id,
                    Node.deleted_at.is_(None),
                )
            )
        )
        result = await self.session.execute(stmt)
        return result.all()

    async def update_acl(self, acl: ACL) -> ACL:
        """Update an ACL entry."""
        await self.session.flush()
        await self.session.refresh(acl)
        return acl

    async def delete_acl(self, acl: ACL) -> None:
        """Delete an ACL entry."""
        await self.session.delete(acl)
        await self.session.flush()

    async def delete_by_object_and_user(self, object_id: str, user_id: str) -> None:
        """Delete ACL for a specific object/user pair."""
        acl = await self.get_acl(object_id, user_id)
        if acl:
            await self.delete_acl(acl)

    async def delete_acls_for_object(self, object_id: str) -> int:
        """
        Delete all ACL entries for an object.

        Returns:
            Number of deleted entries
        """
        stmt = select(ACL).where(ACL.object_id == object_id)
        result = await self.session.execute(stmt)
        acls = result.scalars().all()

        for acl in acls:
            await self.session.delete(acl)

        await self.session.flush()
        return len(acls)

    async def check_permission(
        self, object_id: str, user_id: str, required_permission: Permission
    ) -> bool:
        """
        Check if user has required permission on object.

        Args:
            object_id: Object ID
            user_id: User ID
            required_permission: Required permission level

        Returns:
            True if user has permission
        """
        acl = await self.get_acl(object_id, user_id)
        if acl is None:
            return False

        permission_hierarchy = {
            "owner": 5,
            "admin": 4,
            "editor": 3,
            "commenter": 2,
            "viewer": 1,
        }

        permission_value = (
            acl.permission.value
            if isinstance(acl.permission, Permission)
            else str(acl.permission)
        )
        required_value = (
            required_permission.value
            if isinstance(required_permission, Permission)
            else str(required_permission)
        )

        user_level = permission_hierarchy.get(permission_value, 0)
        required_level = permission_hierarchy.get(required_value, 0)

        return user_level >= required_level

    # === Share Link Operations ===

    async def create_share_link(self, link: ShareLink) -> ShareLink:
        """Create a new share link."""
        self.session.add(link)
        await self.session.flush()
        return link

    async def get_share_link_by_id(self, link_id: str) -> ShareLink | None:
        """Get share link by ID."""
        stmt = select(ShareLink).where(ShareLink.id == link_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_share_link_by_token(self, token: str) -> ShareLink | None:
        """Get share link by token."""
        stmt = select(ShareLink).where(
            and_(ShareLink.token == token, ShareLink.is_active == True)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_share_links_for_object(self, object_id: str) -> Sequence[ShareLink]:
        """Get all share links for an object."""
        stmt = select(ShareLink).where(ShareLink.object_id == object_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_share_link(self, link: ShareLink) -> ShareLink:
        """Update a share link."""
        await self.session.flush()
        await self.session.refresh(link)
        return link

    async def delete_share_link(self, link: ShareLink) -> None:
        """Delete a share link."""
        await self.session.delete(link)
        await self.session.flush()

    async def get_expired_links(self, limit: int = 100) -> Sequence[ShareLink]:
        """
        Get expired share links for cleanup.

        Args:
            limit: Maximum results

        Returns:
            List of expired links
        """
        from datetime import datetime

        stmt = (
            select(ShareLink)
            .where(
                and_(
                    ShareLink.expires_at.isnot(None),
                    ShareLink.expires_at < datetime.utcnow(),
                    ShareLink.is_active == True,
                )
            )
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
