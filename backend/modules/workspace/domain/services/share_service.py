"""
Share service for managing permissions and share links.
"""

import secrets
import uuid
from datetime import datetime
from hashlib import sha256

from sqlalchemy.ext.asyncio import AsyncSession

from workspace.db.repos.acl_repo import ACLRepository
from workspace.db.repos.node_repo import NodeRepository
from workspace.db.tables.acl import ACL, ShareLink
from workspace.domain.models.acl import (
    ChangeRoleCommand,
    CreateShareLinkCommand,
    RevokeShareCommand,
    RevokeShareLinkCommand,
    ShareCommand,
)
from workspace.domain.models.types import Permission
from workspace.domain.policies.permissions import PermissionPolicy
from workspace.domain.services.node_service import (
    NodeNotFoundError,
    NodeServiceError,
    PermissionDeniedError,
)
from workspace.events.bus import EventBus, publish_acl_revoked, publish_acl_shared


class ShareService:
    """
    Share service for permission management.

    Handles sharing nodes with users and creating share links.
    """

    def __init__(
        self,
        session: AsyncSession,
        node_repo: NodeRepository,
        acl_repo: ACLRepository,
        event_bus: EventBus,
    ) -> None:
        """
        Initialize service.

        Args:
            session: Database session
            node_repo: Node repository
            acl_repo: ACL repository
            event_bus: Event bus
        """
        self.session = session
        self.node_repo = node_repo
        self.acl_repo = acl_repo
        self.event_bus = event_bus

    async def share_with_user(
        self, command: ShareCommand, actor_id: str
    ) -> ACL:
        """
        Share a node with a user.

        Args:
            command: Share command
            actor_id: User performing the share

        Returns:
            Created ACL entry

        Raises:
            NodeNotFoundError: If node not found
            PermissionDeniedError: If actor cannot share
        """
        # Load node
        node = await self.node_repo.get_by_id(command.object_id)
        if node is None:
            raise NodeNotFoundError(f"Node {command.object_id} not found")

        # Check if actor can manage ACL
        actor_acl = await self.acl_repo.get_acl(command.object_id, actor_id)
        from workspace.domain.models.node import NodeModel

        node_model = NodeModel(
            id=node.id,
            node_type=node.node_type,
            title=node.title,
            owner_id=node.owner_id,
            visibility=node.visibility,
            parent_id=node.parent_id,
            path=node.path,
            depth=node.depth,
            version=node.version,
            created_at=node.created_at,
            updated_at=node.updated_at,
            deleted_at=node.deleted_at,
            description=node.description,
            layout=node.layout,
        )

        actor_acl_model = None
        if actor_acl:
            from workspace.domain.models.acl import ACLModel

            actor_acl_model = ACLModel(
                id=actor_acl.id,
                object_id=actor_acl.object_id,
                user_id=actor_acl.user_id,
                permission=actor_acl.permission,
                inherit_to_children=actor_acl.inherit_to_children,
                is_inherited=actor_acl.is_inherited,
                inherited_from=actor_acl.inherited_from,
                granted_by=actor_acl.granted_by,
                created_at=actor_acl.created_at,
                updated_at=actor_acl.updated_at,
            )

        if not node.owner_id == actor_id:
            if not PermissionPolicy.can_share(node_model, actor_id, actor_acl_model):
                raise PermissionDeniedError("Cannot share this node")

        # Check if ACL already exists
        existing = await self.acl_repo.get_acl(command.object_id, command.user_id)
        if existing is not None:
            # Update existing permission
            existing.permission = command.permission
            existing.inherit_to_children = command.inherit_to_children
            acl = await self.acl_repo.update_acl(existing)
        else:
            # Create new ACL
            acl = ACL(
                id=str(uuid.uuid4()),
                object_id=command.object_id,
                user_id=command.user_id,
                permission=command.permission,
                inherit_to_children=command.inherit_to_children,
                is_inherited=False,
                granted_by=command.granted_by,
            )
            acl = await self.acl_repo.create_acl(acl)

        # Publish event
        workspace_id = self._get_workspace_id(node.path)
        await publish_acl_shared(
            self.event_bus,
            actor_id=actor_id,
            object_id=command.object_id,
            user_id=command.user_id,
            permission=command.permission.value,
            workspace_id=workspace_id,
        )

        return acl

    async def revoke_share(
        self, command: RevokeShareCommand, actor_id: str
    ) -> None:
        """
        Revoke a user's access to a node.

        Args:
            command: Revoke command
            actor_id: User performing the revoke

        Raises:
            NodeNotFoundError: If node not found
            PermissionDeniedError: If actor cannot revoke
        """
        # Load node
        node = await self.node_repo.get_by_id(command.object_id)
        if node is None:
            raise NodeNotFoundError(f"Node {command.object_id} not found")

        # Check permissions
        if node.owner_id != actor_id:
            actor_acl = await self.acl_repo.get_acl(command.object_id, actor_id)
            if actor_acl is None or actor_acl.permission not in {
                Permission.OWNER,
                Permission.ADMIN,
            }:
                raise PermissionDeniedError("Cannot revoke access to this node")

        # Get and delete ACL
        acl = await self.acl_repo.get_acl(command.object_id, command.user_id)
        if acl is not None:
            await self.acl_repo.delete_acl(acl)

        # Publish event
        workspace_id = self._get_workspace_id(node.path)
        await publish_acl_revoked(
            self.event_bus,
            actor_id=actor_id,
            object_id=command.object_id,
            user_id=command.user_id,
            workspace_id=workspace_id,
        )

    async def change_role(
        self, command: ChangeRoleCommand, actor_id: str
    ) -> ACL:
        """
        Change a user's permission level.

        Args:
            command: Change role command
            actor_id: User performing the change

        Returns:
            Updated ACL entry
        """
        # Load node
        node = await self.node_repo.get_by_id(command.object_id)
        if node is None:
            raise NodeNotFoundError(f"Node {command.object_id} not found")

        # Check permissions
        if node.owner_id != actor_id:
            actor_acl = await self.acl_repo.get_acl(command.object_id, actor_id)
            if actor_acl is None or actor_acl.permission not in {
                Permission.OWNER,
                Permission.ADMIN,
            }:
                raise PermissionDeniedError("Cannot change permissions on this node")

        # Get ACL
        acl = await self.acl_repo.get_acl(command.object_id, command.user_id)
        if acl is None:
            raise NodeServiceError(f"User {command.user_id} does not have access")

        # Update permission
        acl.permission = command.new_permission
        acl = await self.acl_repo.update_acl(acl)

        return acl

    async def create_share_link(
        self, command: CreateShareLinkCommand, actor_id: str
    ) -> ShareLink:
        """
        Create a shareable link.

        Args:
            command: Create link command
            actor_id: User creating the link

        Returns:
            Created share link
        """
        # Load node
        node = await self.node_repo.get_by_id(command.object_id)
        if node is None:
            raise NodeNotFoundError(f"Node {command.object_id} not found")

        # Check permissions
        if node.owner_id != actor_id:
            actor_acl = await self.acl_repo.get_acl(command.object_id, actor_id)
            if actor_acl is None or actor_acl.permission not in {
                Permission.OWNER,
                Permission.ADMIN,
            }:
                raise PermissionDeniedError("Cannot create share link for this node")

        # Generate secure token
        token = secrets.token_urlsafe(32)

        # Hash password if provided
        password_hash = None
        if command.password is not None:
            password_hash = sha256(command.password.encode()).hexdigest()

        # Create share link
        link = ShareLink(
            id=str(uuid.uuid4()),
            object_id=command.object_id,
            token=token,
            permission=command.permission,
            password_hash=password_hash,
            expires_at=command.expires_at,
            created_by=command.created_by,
            is_active=True,
            access_count=0,
        )

        link = await self.acl_repo.create_share_link(link)
        return link

    async def revoke_share_link(
        self, command: RevokeShareLinkCommand, actor_id: str
    ) -> None:
        """
        Revoke a share link.

        Args:
            command: Revoke command
            actor_id: User revoking the link
        """
        link = await self.acl_repo.get_share_link_by_id(command.link_id)
        if link is None:
            raise NodeServiceError(f"Share link {command.link_id} not found")

        # Check permissions
        node = await self.node_repo.get_by_id(link.object_id)
        if node is None:
            raise NodeNotFoundError(f"Node {link.object_id} not found")

        if node.owner_id != actor_id and link.created_by != actor_id:
            raise PermissionDeniedError("Cannot revoke this share link")

        # Deactivate link
        link.is_active = False
        await self.acl_repo.update_share_link(link)

    async def get_share_link_by_token(self, token: str) -> ShareLink | None:
        """Get share link by token."""
        return await self.acl_repo.get_share_link_by_token(token)

    async def validate_share_link_password(
        self, link: ShareLink, password: str
    ) -> bool:
        """
        Validate share link password.

        Args:
            link: Share link
            password: Password to validate

        Returns:
            True if valid
        """
        if link.password_hash is None:
            return True

        password_hash = sha256(password.encode()).hexdigest()
        return password_hash == link.password_hash

    async def get_shared_with_user(
        self, user_id: str
    ) -> list[tuple[ACL, any]]:
        """
        Get all nodes shared with a user.

        Uses a join to avoid N+1 query problem.

        Args:
            user_id: User ID

        Returns:
            List of (ACL, Node) tuples
        """
        # Use repository method with join to avoid N+1 queries
        return await self.acl_repo.get_acls_with_nodes_for_user(user_id)

    def _get_workspace_id(self, path: str) -> str | None:
        """Extract workspace ID from path."""
        parts = path.strip("/").split("/")
        if parts:
            return parts[0]
        return None
