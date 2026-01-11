"""
Node table definition.

Nodes represent the workspace tree structure: workspace → folder → study
"""

from typing import Any

from sqlalchemy import JSON, Boolean, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from workspace.db.base import Base, SoftDeleteMixin, TimestampMixin
from workspace.domain.models.types import NodeType, Visibility


class Node(Base, TimestampMixin, SoftDeleteMixin):
    """
    Node in the workspace tree.

    Supports three types: workspace, folder, study
    Folders can nest infinitely via parent_id self-reference.
    """

    __tablename__ = "nodes"

    # Primary key
    id: Mapped[str] = mapped_column(String(64), primary_key=True)

    # Node type
    node_type: Mapped[NodeType] = mapped_column(String(20), nullable=False)

    # Basic metadata
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Owner
    owner_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    # Visibility
    visibility: Mapped[Visibility] = mapped_column(
        String(20), nullable=False, default=Visibility.PRIVATE
    )

    # Tree structure
    parent_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("nodes.id", ondelete="CASCADE"), nullable=True, index=True
    )

    # Materialized path for efficient tree queries
    # Format: /root_id/parent_id/node_id/
    # Enables fast "get all descendants" queries
    path: Mapped[str] = mapped_column(String(1000), nullable=False, index=True)

    # Depth in tree (0 = workspace, 1 = direct child, etc.)
    depth: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Layout metadata (for UI positioning)
    # Stores: {x: float, y: float, z: int, group: str?, viewMode: str?}
    layout: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    # Version for optimistic locking
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Relationships
    parent: Mapped["Node | None"] = relationship(
        "Node", remote_side=[id], back_populates="children"
    )
    children: Mapped[list["Node"]] = relationship(
        "Node", back_populates="parent", cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        # Fast owner queries
        Index("ix_nodes_owner_type", "owner_id", "node_type"),
        # Fast tree path queries (get all descendants)
        Index("ix_nodes_path_prefix", "path", postgresql_using="gin", postgresql_ops={"path": "gin_trgm_ops"}),
        # Fast soft-delete filtering
        Index("ix_nodes_deleted_at", "deleted_at"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Node(id={self.id}, type={self.node_type}, title={self.title})>"

    @property
    def is_workspace(self) -> bool:
        """Check if node is a workspace."""
        return self.node_type == NodeType.WORKSPACE

    @property
    def is_folder(self) -> bool:
        """Check if node is a folder."""
        return self.node_type == NodeType.FOLDER

    @property
    def is_study(self) -> bool:
        """Check if node is a study."""
        return self.node_type == NodeType.STUDY

    def update_path(self) -> None:
        """
        Update materialized path based on parent.

        Must be called after parent changes.
        """
        if self.parent_id is None:
            # Root node (workspace)
            self.path = f"/{self.id}/"
            self.depth = 0
        else:
            # Child node
            if self.parent is None:
                raise ValueError("Parent not loaded, cannot compute path")
            self.path = f"{self.parent.path}{self.id}/"
            self.depth = self.parent.depth + 1

    def is_ancestor_of(self, other: "Node") -> bool:
        """
        Check if this node is an ancestor of another node.

        Args:
            other: Potential descendant node

        Returns:
            True if this node is an ancestor
        """
        return other.path.startswith(self.path) and other.id != self.id

    def is_descendant_of(self, other: "Node") -> bool:
        """
        Check if this node is a descendant of another node.

        Args:
            other: Potential ancestor node

        Returns:
            True if this node is a descendant
        """
        return self.path.startswith(other.path) and self.id != other.id
