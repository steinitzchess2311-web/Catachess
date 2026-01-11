"""
Node domain model.

This is the aggregate root for workspace/folder/study objects.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from workspace.domain.models.types import NodeType, Visibility


@dataclass
class NodeModel:
    """
    Domain model for Node.

    Represents a node in the workspace tree (workspace/folder/study).
    This is a pure domain object, separate from ORM concerns.
    """

    id: str
    node_type: NodeType
    title: str
    owner_id: str
    visibility: Visibility
    parent_id: str | None
    path: str
    depth: int
    version: int
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None
    description: str | None = None
    layout: dict[str, Any] = field(default_factory=dict)

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

    @property
    def is_root(self) -> bool:
        """Check if node is a root (workspace without parent)."""
        return self.parent_id is None

    @property
    def is_deleted(self) -> bool:
        """Check if node is soft-deleted."""
        return self.deleted_at is not None

    def compute_path(self, parent_path: str | None) -> str:
        """
        Compute materialized path.

        Args:
            parent_path: Path of parent node (None if root)

        Returns:
            Computed path
        """
        if parent_path is None:
            return f"/{self.id}/"
        return f"{parent_path}{self.id}/"

    def compute_depth(self, parent_depth: int | None) -> int:
        """
        Compute depth in tree.

        Args:
            parent_depth: Depth of parent node (None if root)

        Returns:
            Computed depth
        """
        if parent_depth is None:
            return 0
        return parent_depth + 1

    def is_ancestor_of_path(self, other_path: str) -> bool:
        """
        Check if this node is an ancestor of another node (by path).

        Args:
            other_path: Path of potential descendant

        Returns:
            True if this node is an ancestor
        """
        return other_path.startswith(self.path) and other_path != self.path

    def is_descendant_of_path(self, other_path: str) -> bool:
        """
        Check if this node is a descendant of another node (by path).

        Args:
            other_path: Path of potential ancestor

        Returns:
            True if this node is a descendant
        """
        return self.path.startswith(other_path) and self.path != other_path


@dataclass
class CreateNodeCommand:
    """Command to create a new node."""

    node_type: NodeType
    title: str
    owner_id: str
    parent_id: str | None = None
    description: str | None = None
    visibility: Visibility = Visibility.PRIVATE
    layout: dict[str, Any] = field(default_factory=dict)


@dataclass
class UpdateNodeCommand:
    """Command to update a node."""

    node_id: str
    title: str | None = None
    description: str | None = None
    visibility: Visibility | None = None
    layout: dict[str, Any] | None = None
    version: int | None = None  # For optimistic locking


@dataclass
class MoveNodeCommand:
    """Command to move a node to a new parent."""

    node_id: str
    new_parent_id: str | None
    version: int  # For optimistic locking


@dataclass
class DeleteNodeCommand:
    """Command to delete a node (soft delete)."""

    node_id: str
    version: int  # For optimistic locking


@dataclass
class RestoreNodeCommand:
    """Command to restore a soft-deleted node."""

    node_id: str
