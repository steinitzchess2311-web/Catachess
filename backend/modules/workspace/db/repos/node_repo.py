"""
Node repository for database operations.
"""

from typing import Sequence

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from modules.workspace.db.tables.nodes import Node
from modules.workspace.domain.models.types import NodeType


class NodeRepository:
    """
    Repository for Node database operations.

    Handles all database access for nodes, including tree queries.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize repository.

        Args:
            session: Database session
        """
        self.session = session

    async def create(self, node: Node) -> Node:
        """
        Create a new node.

        Args:
            node: Node to create

        Returns:
            Created node
        """
        if not node.path:
            if node.parent_id:
                parent = await self.get_by_id(node.parent_id, include_deleted=True)
                if parent:
                    node.path = f"{parent.path}{node.id}/"
                    node.depth = parent.depth + 1
                else:
                    node.path = f"/{node.id}/"
                    node.depth = 0
            else:
                node.path = f"/{node.id}/"
                node.depth = 0

        self.session.add(node)
        await self.session.flush()
        return node

    async def get_by_id(self, node_id: str, include_deleted: bool = False) -> Node | None:
        """
        Get node by ID.

        Args:
            node_id: Node ID
            include_deleted: Whether to include soft-deleted nodes

        Returns:
            Node or None if not found
        """
        stmt = select(Node).where(Node.id == node_id)

        if not include_deleted:
            stmt = stmt.where(Node.deleted_at.is_(None))

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_ids(
        self, node_ids: list[str], include_deleted: bool = False
    ) -> Sequence[Node]:
        """
        Get multiple nodes by IDs.

        Args:
            node_ids: List of node IDs
            include_deleted: Whether to include soft-deleted nodes

        Returns:
            List of nodes
        """
        stmt = select(Node).where(Node.id.in_(node_ids))

        if not include_deleted:
            stmt = stmt.where(Node.deleted_at.is_(None))

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_children(
        self, parent_id: str, include_deleted: bool = False
    ) -> Sequence[Node]:
        """
        Get direct children of a node.

        Args:
            parent_id: Parent node ID
            include_deleted: Whether to include soft-deleted nodes

        Returns:
            List of child nodes
        """
        stmt = select(Node).where(Node.parent_id == parent_id)

        if not include_deleted:
            stmt = stmt.where(Node.deleted_at.is_(None))

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_descendants(
        self, node_path: str, include_deleted: bool = False
    ) -> Sequence[Node]:
        """
        Get all descendants of a node (using materialized path).

        Args:
            node_path: Path of the node
            include_deleted: Whether to include soft-deleted nodes

        Returns:
            List of descendant nodes
        """
        # Use path prefix matching for efficient tree queries
        stmt = select(Node).where(Node.path.startswith(node_path), Node.path != node_path)

        if not include_deleted:
            stmt = stmt.where(Node.deleted_at.is_(None))

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_owner(
        self, owner_id: str, node_type: NodeType | None = None, include_deleted: bool = False
    ) -> Sequence[Node]:
        """
        Get nodes owned by user.

        Args:
            owner_id: Owner user ID
            node_type: Optional filter by node type
            include_deleted: Whether to include soft-deleted nodes

        Returns:
            List of nodes
        """
        conditions = [Node.owner_id == owner_id]

        if node_type is not None:
            conditions.append(Node.node_type == node_type)

        if not include_deleted:
            conditions.append(Node.deleted_at.is_(None))

        stmt = select(Node).where(and_(*conditions))
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_root_nodes(
        self, owner_id: str, include_deleted: bool = False
    ) -> Sequence[Node]:
        """
        Get root nodes (nodes without parent).

        Args:
            owner_id: Owner user ID
            include_deleted: Whether to include soft-deleted nodes

        Returns:
            List of root nodes
        """
        conditions = [
            Node.owner_id == owner_id,
            Node.parent_id.is_(None),
        ]

        if not include_deleted:
            conditions.append(Node.deleted_at.is_(None))

        stmt = select(Node).where(and_(*conditions))
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update(self, node: Node) -> Node:
        """
        Update a node.

        Args:
            node: Node with updated fields

        Returns:
            Updated node
        """
        await self.session.flush()
        await self.session.refresh(node)
        return node

    async def delete(self, node: Node) -> None:
        """
        Permanently delete a node.

        Args:
            node: Node to delete
        """
        await self.session.delete(node)
        await self.session.flush()

    async def count_by_owner(self, owner_id: str, node_type: NodeType | None = None) -> int:
        """
        Count nodes owned by user.

        Args:
            owner_id: Owner user ID
            node_type: Optional filter by node type

        Returns:
            Count of nodes
        """
        from sqlalchemy import func as sqlfunc

        conditions = [Node.owner_id == owner_id, Node.deleted_at.is_(None)]

        if node_type is not None:
            conditions.append(Node.node_type == node_type)

        stmt = select(sqlfunc.count(Node.id)).where(and_(*conditions))
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def search_by_title(
        self, title_query: str, owner_id: str | None = None, limit: int = 50
    ) -> Sequence[Node]:
        """
        Search nodes by title.

        Args:
            title_query: Title search query
            owner_id: Optional owner filter
            limit: Maximum results

        Returns:
            List of matching nodes
        """
        conditions = [
            Node.title.ilike(f"%{title_query}%"),
            Node.deleted_at.is_(None),
        ]

        if owner_id is not None:
            conditions.append(Node.owner_id == owner_id)

        stmt = select(Node).where(and_(*conditions)).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def search_by_name(
        self,
        query: str,
        node_type: str | None = None,
        owner_id: str | None = None,
        limit: int = 50,
    ) -> Sequence[Node]:
        """
        Search nodes by name (title).

        Args:
            query: Name search query
            node_type: Optional node type filter
            owner_id: Optional owner filter
            limit: Maximum results

        Returns:
            List of matching nodes
        """
        conditions = [
            Node.title.ilike(f"%{query}%"),
            Node.deleted_at.is_(None),
        ]

        if node_type is not None:
            conditions.append(Node.node_type == node_type)

        if owner_id is not None:
            conditions.append(Node.owner_id == owner_id)

        stmt = select(Node).where(and_(*conditions)).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()
