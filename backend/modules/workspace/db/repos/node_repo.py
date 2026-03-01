"""
Node repository for database operations.
"""

from typing import Sequence

from sqlalchemy import and_, or_, select, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, selectinload

from modules.workspace.db.tables.acl import ACL
from modules.workspace.db.tables.nodes import Node
from modules.workspace.domain.models.types import NodeType, Visibility


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
            Node.visibility != Visibility.SHARED,
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

    async def get_trash_roots(self, owner_id: str) -> Sequence[Node]:
        """Return top-level deleted items (roots of each deletion group)."""
        stmt = (
            select(Node)
            .where(
                Node.owner_id == owner_id,
                Node.deleted_root_id == Node.id,
                Node.deleted_at.isnot(None),
            )
            .order_by(Node.deleted_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def cascade_trash(self, root_path: str, root_id: str, deleted_at) -> None:
        """Soft-delete + tag all descendants with the root's deleted_root_id."""
        stmt = (
            sa_update(Node)
            .where(
                Node.path.startswith(root_path),
                Node.path != root_path,
                Node.deleted_at.is_(None),
            )
            .values(deleted_at=deleted_at, deleted_root_id=root_id)
        )
        await self.session.execute(stmt)

    async def cascade_restore(self, root_id: str) -> None:
        """Clear deleted_at and deleted_root_id for entire deletion group."""
        stmt = (
            sa_update(Node)
            .where(Node.deleted_root_id == root_id)
            .values(deleted_at=None, deleted_root_id=None)
        )
        await self.session.execute(stmt)

    async def bulk_update_paths(self, old_path: str, new_path: str) -> None:
        """
        Atomically rewrite paths for all descendants after a node move.

        Replaces the old path prefix with the new one using a single SQL UPDATE
        instead of loading all descendants and updating them one-by-one (N+1).

        Also recomputes depth from the new path (depth = number of '/' chars - 2).
        """
        from sqlalchemy import text, func as sqlfunc

        # Use regexp_replace to swap the leading old_path with new_path in one statement.
        # PostgreSQL: regexp_replace(path, '^<escaped>', new_path)
        # We escape the old_path to avoid regex metacharacter issues.
        escaped = old_path.replace("/", "\\/")
        await self.session.execute(
            sa_update(Node)
            .where(
                Node.path.startswith(old_path),
                Node.path != old_path,
            )
            .values(
                path=text(
                    f"regexp_replace(path, '^{escaped}', '{new_path}')"
                ),
                depth=text(
                    f"length(regexp_replace(path, '^{escaped}', '{new_path}')) "
                    f"- length(replace(regexp_replace(path, '^{escaped}', '{new_path}'), '/', '')) - 2"
                ),
            )
        )

    async def cascade_visibility(self, node_path: str, visibility: Visibility) -> None:
        """
        Bulk-update visibility of all descendants of a node.

        Called after changing a node's own visibility so the entire subtree
        reflects the new state. Uses path-prefix matching for efficiency.
        """
        await self.session.execute(
            sa_update(Node)
            .where(
                Node.path.like(node_path + "%"),
                Node.path != node_path,
                Node.deleted_at.is_(None),
            )
            .values(visibility=visibility)
        )

    async def get_public_studies(
        self, limit: int = 20, offset: int = 0
    ) -> Sequence[Node]:
        """
        Get public study nodes, ordered by most recently created.

        With cascade-based visibility, a study is public iff visibility='public'.
        """
        stmt = (
            select(Node)
            .where(
                Node.node_type == NodeType.STUDY,
                Node.visibility == Visibility.PUBLIC,
                Node.deleted_at.is_(None),
            )
            .order_by(Node.created_at.desc())
            .limit(min(limit, 100))
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    def _is_publicly_accessible(self, node: Node) -> bool:
        """Return True if node has visibility=public.

        With cascade-based visibility inheritance, the DB value is always the
        effective visibility — no ancestor traversal needed.
        """
        return node.visibility == Visibility.PUBLIC

    async def get_public_nodes(
        self, parent_id: str | None = None, limit: int = 40, offset: int = 0
    ) -> Sequence[Node]:
        """
        Get publicly browseable nodes.

        Root view (parent_id omitted / "root*"):
          Returns every "public island entry point" — a public node whose parent
          is either absent (true root) or non-public (private parent).
          When a user later makes the parent public (cascade), that node is no longer
          an entry point and naturally disappears from this list, reappearing inside
          its parent's tree.

        Child view (parent_id = UUID):
          Returns direct public children of the given public folder.
        """
        is_root = parent_id is None or str(parent_id).startswith("root")

        if is_root:
            # LEFT JOIN with parent to detect "public island entry points":
            # visible iff node is public AND (no parent OR parent is not public)
            parent_alias = aliased(Node, flat=True)
            stmt = (
                select(Node)
                .outerjoin(parent_alias, parent_alias.id == Node.parent_id)
                .where(
                    Node.visibility == Visibility.PUBLIC,
                    Node.deleted_at.is_(None),
                    or_(
                        Node.parent_id.is_(None),
                        parent_alias.visibility != Visibility.PUBLIC,
                    ),
                )
                .order_by(Node.created_at.desc())
                .limit(min(limit, 100))
                .offset(offset)
            )
            result = await self.session.execute(stmt)
            return result.scalars().all()

        parent = await self.get_by_id(parent_id)
        if parent is None or not self._is_publicly_accessible(parent):
            return []

        # Only show children that are also public (private subtrees are excluded by cascade)
        stmt = (
            select(Node)
            .where(
                Node.parent_id == parent_id,
                Node.visibility == Visibility.PUBLIC,
                Node.deleted_at.is_(None),
            )
            .order_by(Node.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_shared_nodes(
        self, user_id: str, parent_id: str | None = None
    ) -> Sequence[Node]:
        """
        Get nodes shared with a user.

        - parent_id None or "root*": nodes directly shared (non-inherited ACL)
        - parent_id UUID: direct children of a shared folder
        """
        is_root = parent_id is None or str(parent_id).startswith("root")

        if is_root:
            stmt = (
                select(Node)
                .join(ACL, ACL.object_id == Node.id)
                .where(
                    ACL.user_id == user_id,
                    ACL.is_inherited.is_(False),
                    Node.deleted_at.is_(None),
                )
                .order_by(Node.created_at.desc())
            )
        else:
            stmt = (
                select(Node)
                .where(
                    Node.parent_id == parent_id,
                    Node.deleted_at.is_(None),
                )
                .order_by(Node.created_at.desc())
            )

        result = await self.session.execute(stmt)
        return result.scalars().all()
