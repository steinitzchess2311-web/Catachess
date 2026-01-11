"""
Node service for business logic.

Orchestrates node operations and event publishing.
"""

import uuid
from datetime import datetime
from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from workspace.db.repos.acl_repo import ACLRepository
from workspace.db.repos.node_repo import NodeRepository
from workspace.db.tables.acl import ACL
from workspace.db.tables.nodes import Node
from workspace.domain.models.node import (
    CreateNodeCommand,
    DeleteNodeCommand,
    MoveNodeCommand,
    UpdateNodeCommand,
)
from workspace.domain.models.types import NodeType, Permission, Visibility
from workspace.domain.policies.permissions import PermissionPolicy
from workspace.events.bus import EventBus, publish_node_created, publish_node_deleted, publish_node_moved, publish_node_updated


class NodeServiceError(Exception):
    """Base exception for node service errors."""
    pass


class NodeNotFoundError(NodeServiceError):
    """Node not found."""
    pass


class PermissionDeniedError(NodeServiceError):
    """Permission denied."""
    pass


class InvalidOperationError(NodeServiceError):
    """Invalid operation."""
    pass


class OptimisticLockError(NodeServiceError):
    """Optimistic lock conflict."""
    pass


class NodeService:
    """
    Node service for business operations.

    Handles node creation, updates, moves, and deletions.
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

    async def create_node(
        self, command: CreateNodeCommand, actor_id: str
    ) -> Node:
        """
        Create a new node.

        Args:
            command: Create command
            actor_id: User creating the node

        Returns:
            Created node

        Raises:
            PermissionDeniedError: If actor cannot create under parent
            NodeNotFoundError: If parent not found
        """
        # Validate parent exists and check permissions
        parent: Node | None = None
        if command.parent_id is not None:
            parent = await self.node_repo.get_by_id(command.parent_id)
            if parent is None:
                raise NodeNotFoundError(f"Parent node {command.parent_id} not found")

            # Check if actor can create children under parent
            acl = await self.acl_repo.get_acl(command.parent_id, actor_id)
            if not parent.owner_id == actor_id:
                if acl is None or not PermissionPolicy.can_write(
                    self._node_to_model(parent), actor_id, self._acl_to_model(acl)
                ):
                    raise PermissionDeniedError("Cannot create node under this parent")

        # Create node
        node = Node(
            id=str(uuid.uuid4()),
            node_type=command.node_type,
            title=command.title,
            description=command.description,
            owner_id=command.owner_id,
            visibility=command.visibility,
            parent_id=command.parent_id,
            layout=command.layout,
            version=1,
            path="",  # Will be computed
            depth=0,  # Will be computed
        )

        # Compute path and depth
        if parent is not None:
            node.path = f"{parent.path}{node.id}/"
            node.depth = parent.depth + 1
        else:
            node.path = f"/{node.id}/"
            node.depth = 0

        # Save to database
        node = await self.node_repo.create(node)

        # Publish event
        workspace_id = self._get_workspace_id(node, parent)
        await publish_node_created(
            self.event_bus,
            actor_id=actor_id,
            node_id=node.id,
            node_type=node.node_type,
            parent_id=command.parent_id,
            title=command.title,
            workspace_id=workspace_id,
        )

        await self.session.commit()
        return node

    async def update_node(
        self, command: UpdateNodeCommand, actor_id: str
    ) -> Node:
        """
        Update a node.

        Args:
            command: Update command
            actor_id: User updating the node

        Returns:
            Updated node

        Raises:
            NodeNotFoundError: If node not found
            PermissionDeniedError: If actor cannot update
            OptimisticLockError: If version conflict
        """
        # Load node
        node = await self.node_repo.get_by_id(command.node_id)
        if node is None:
            raise NodeNotFoundError(f"Node {command.node_id} not found")

        # Check permissions
        acl = await self.acl_repo.get_acl(command.node_id, actor_id)
        if not node.owner_id == actor_id:
            if acl is None or not PermissionPolicy.can_write(
                self._node_to_model(node), actor_id, self._acl_to_model(acl)
            ):
                raise PermissionDeniedError("Cannot update this node")

        # Check version (optimistic locking)
        if command.version is not None and node.version != command.version:
            raise OptimisticLockError(
                f"Version conflict: expected {command.version}, got {node.version}"
            )

        # Track changes for event
        changes = {}

        # Apply updates
        if command.title is not None:
            changes["title"] = {"old": node.title, "new": command.title}
            node.title = command.title

        if command.description is not None:
            changes["description"] = {"old": node.description, "new": command.description}
            node.description = command.description

        if command.visibility is not None:
            changes["visibility"] = {"old": node.visibility.value, "new": command.visibility.value}
            node.visibility = command.visibility

        if command.layout is not None:
            changes["layout"] = {"old": node.layout, "new": command.layout}
            node.layout = command.layout

        # Increment version
        node.version += 1

        # Save
        node = await self.node_repo.update(node)

        # Publish event
        workspace_id = await self._get_workspace_id_for_node(node.id)
        await publish_node_updated(
            self.event_bus,
            actor_id=actor_id,
            node_id=node.id,
            node_type=node.node_type,
            version=node.version,
            changes=changes,
            workspace_id=workspace_id,
        )

        await self.session.commit()
        return node

    async def move_node(self, command: MoveNodeCommand, actor_id: str) -> Node:
        """
        Move a node to a new parent.

        Args:
            command: Move command
            actor_id: User moving the node

        Returns:
            Moved node

        Raises:
            NodeNotFoundError: If node or parent not found
            PermissionDeniedError: If actor cannot move
            InvalidOperationError: If move is invalid
            OptimisticLockError: If version conflict
        """
        # Load node
        node = await self.node_repo.get_by_id(command.node_id)
        if node is None:
            raise NodeNotFoundError(f"Node {command.node_id} not found")

        # Check permissions on source
        acl = await self.acl_repo.get_acl(command.node_id, actor_id)
        if not node.owner_id == actor_id:
            if acl is None or not PermissionPolicy.can_move(
                self._node_to_model(node), actor_id, self._acl_to_model(acl)
            ):
                raise PermissionDeniedError("Cannot move this node")

        # Check version
        if node.version != command.version:
            raise OptimisticLockError(
                f"Version conflict: expected {command.version}, got {node.version}"
            )

        # Validate and load new parent
        new_parent: Node | None = None
        if command.new_parent_id is not None:
            new_parent = await self.node_repo.get_by_id(command.new_parent_id)
            if new_parent is None:
                raise NodeNotFoundError(f"Parent {command.new_parent_id} not found")

            # Cannot move to self or descendant
            if new_parent.path.startswith(node.path):
                raise InvalidOperationError("Cannot move node to itself or descendant")

            # Check permissions on destination
            parent_acl = await self.acl_repo.get_acl(command.new_parent_id, actor_id)
            if not new_parent.owner_id == actor_id:
                if parent_acl is None or not PermissionPolicy.can_create_child(
                    self._node_to_model(new_parent), actor_id, self._acl_to_model(parent_acl)
                ):
                    raise PermissionDeniedError("Cannot create nodes under new parent")

        # Store old values
        old_parent_id = node.parent_id
        old_path = node.path

        # Update node
        node.parent_id = command.new_parent_id
        if new_parent is not None:
            node.path = f"{new_parent.path}{node.id}/"
            node.depth = new_parent.depth + 1
        else:
            node.path = f"/{node.id}/"
            node.depth = 0

        node.version += 1

        # Update descendants' paths
        await self._update_descendant_paths(node, old_path)

        # Save
        node = await self.node_repo.update(node)

        # Publish event
        workspace_id = await self._get_workspace_id_for_node(node.id)
        await publish_node_moved(
            self.event_bus,
            actor_id=actor_id,
            node_id=node.id,
            node_type=node.node_type,
            old_parent_id=old_parent_id,
            new_parent_id=command.new_parent_id,
            old_path=old_path,
            new_path=node.path,
            version=node.version,
            workspace_id=workspace_id,
        )

        await self.session.commit()
        return node

    async def delete_node(self, command: DeleteNodeCommand, actor_id: str) -> Node:
        """
        Soft delete a node.

        Args:
            command: Delete command
            actor_id: User deleting the node

        Returns:
            Deleted node

        Raises:
            NodeNotFoundError: If node not found
            PermissionDeniedError: If actor cannot delete
            OptimisticLockError: If version conflict
        """
        # Load node
        node = await self.node_repo.get_by_id(command.node_id)
        if node is None:
            raise NodeNotFoundError(f"Node {command.node_id} not found")

        # Check permissions
        acl = await self.acl_repo.get_acl(command.node_id, actor_id)
        if not node.owner_id == actor_id:
            if acl is None or not PermissionPolicy.can_delete(
                self._node_to_model(node), actor_id, self._acl_to_model(acl)
            ):
                raise PermissionDeniedError("Cannot delete this node")

        # Check version
        if node.version != command.version:
            raise OptimisticLockError(
                f"Version conflict: expected {command.version}, got {node.version}"
            )

        # Soft delete
        node.soft_delete()
        node.version += 1

        # Save
        node = await self.node_repo.update(node)

        # Publish event
        workspace_id = await self._get_workspace_id_for_node(node.id)
        await publish_node_deleted(
            self.event_bus,
            actor_id=actor_id,
            node_id=node.id,
            node_type=node.node_type,
            version=node.version,
            workspace_id=workspace_id,
        )

        await self.session.commit()
        return node

    async def restore_node(self, node_id: str, actor_id: str) -> Node:
        """
        Restore a soft-deleted node.

        Args:
            node_id: Node to restore
            actor_id: User restoring

        Returns:
            Restored node
        """
        node = await self.node_repo.get_by_id(node_id, include_deleted=True)
        if node is None:
            raise NodeNotFoundError(f"Node {node_id} not found")

        if not node.is_deleted:
            raise InvalidOperationError("Node is not deleted")

        # Only owner can restore
        if node.owner_id != actor_id:
            raise PermissionDeniedError("Only owner can restore node")

        node.restore()
        node.version += 1

        node = await self.node_repo.update(node)
        await self.session.commit()
        return node

    async def get_node(self, node_id: str, actor_id: str) -> Node:
        """Get node with permission check."""
        node = await self.node_repo.get_by_id(node_id)
        if node is None:
            raise NodeNotFoundError(f"Node {node_id} not found")

        acl = await self.acl_repo.get_acl(node_id, actor_id)
        if not node.owner_id == actor_id:
            if acl is None or not PermissionPolicy.can_read(
                self._node_to_model(node), actor_id, self._acl_to_model(acl)
            ):
                raise PermissionDeniedError("Cannot read this node")

        return node

    async def get_children(self, parent_id: str, actor_id: str) -> Sequence[Node]:
        """Get children of a node."""
        parent = await self.get_node(parent_id, actor_id)
        return await self.node_repo.get_children(parent_id)

    async def _update_descendant_paths(self, node: Node, old_path: str) -> None:
        """Update paths of all descendants after move."""
        descendants = await self.node_repo.get_descendants(old_path)
        for desc in descendants:
            # Replace old path prefix with new path
            desc.path = desc.path.replace(old_path, node.path, 1)
            desc.depth = desc.path.count("/") - 2
            await self.node_repo.update(desc)

    async def _get_workspace_id_for_node(self, node_id: str) -> str | None:
        """Get workspace ID for a node."""
        node = await self.node_repo.get_by_id(node_id)
        if node is None:
            return None
        return self._get_workspace_id(node, None)

    def _get_workspace_id(self, node: Node, parent: Node | None) -> str | None:
        """Extract workspace ID from node path."""
        if node.node_type == NodeType.WORKSPACE:
            return node.id

        # Extract first ID from path (/workspace_id/...)
        parts = node.path.strip("/").split("/")
        if parts:
            return parts[0]

        if parent is not None and parent.node_type == NodeType.WORKSPACE:
            return parent.id

        return None

    def _node_to_model(self, node: Node):
        """Convert ORM node to domain model."""
        from workspace.domain.models.node import NodeModel
        return NodeModel(
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

    def _acl_to_model(self, acl: ACL):
        """Convert ORM ACL to domain model."""
        from workspace.domain.models.acl import ACLModel
        return ACLModel(
            id=acl.id,
            object_id=acl.object_id,
            user_id=acl.user_id,
            permission=acl.permission,
            inherit_to_children=acl.inherit_to_children,
            is_inherited=acl.is_inherited,
            inherited_from=acl.inherited_from,
            granted_by=acl.granted_by,
            created_at=acl.created_at,
            updated_at=acl.updated_at,
        )
