"""
Variation domain model.

Variations represent nodes in the chess move tree structure.
"""

from dataclasses import dataclass
from datetime import datetime

from workspace.db.tables.variations import VariationPriority, VariationVisibility


@dataclass
class VariationModel:
    """
    Variation domain model.

    Represents a single move in the variation tree.
    """

    id: str
    chapter_id: str
    parent_id: str | None
    next_id: str | None
    move_number: int
    color: str  # 'white' or 'black'
    san: str  # Standard Algebraic Notation
    uci: str  # Universal Chess Interface
    fen: str  # FEN position after this move
    rank: int
    priority: VariationPriority
    visibility: VariationVisibility
    pinned: bool
    created_by: str
    created_at: datetime
    updated_at: datetime

    @property
    def is_main_line(self) -> bool:
        """Check if this is the main line (rank 0)."""
        return self.rank == 0

    @property
    def is_white_move(self) -> bool:
        """Check if this is a white move."""
        return self.color == "white"

    @property
    def is_black_move(self) -> bool:
        """Check if this is a black move."""
        return self.color == "black"

    @property
    def is_pinned(self) -> bool:
        """Check if variation is pinned (won't be auto-reordered)."""
        return self.pinned


@dataclass
class AddMoveCommand:
    """
    Command to add a move to the variation tree.

    Args:
        chapter_id: Chapter ID
        parent_id: Parent move ID (None for first move)
        san: Standard Algebraic Notation
        uci: Universal Chess Interface notation
        fen: FEN position after this move
        move_number: Full move number
        color: 'white' or 'black'
        created_by: User ID adding the move
        rank: Optional rank (default 0 for main line)
        priority: Optional priority (default MAIN)
        visibility: Optional visibility (default PUBLIC)
    """

    chapter_id: str
    parent_id: str | None
    san: str
    uci: str
    fen: str
    move_number: int
    color: str
    created_by: str
    rank: int = 0
    priority: VariationPriority = VariationPriority.MAIN
    visibility: VariationVisibility = VariationVisibility.PUBLIC


@dataclass
class DeleteMoveCommand:
    """
    Command to delete a move from the variation tree.

    Deletes the move and all its descendants.

    Args:
        variation_id: Variation ID to delete
        actor_id: User ID performing deletion
    """

    variation_id: str
    actor_id: str


@dataclass
class PromoteVariationCommand:
    """
    Command to promote a variation to main line.

    Swaps the ranks of the variation and current main line.

    Args:
        variation_id: Variation ID to promote
        actor_id: User ID performing promotion
        expected_version: Expected version for optimistic locking (optional)
    """

    variation_id: str
    actor_id: str
    expected_version: int | None = None


@dataclass
class DemoteVariationCommand:
    """
    Command to demote a main line to variation.

    Swaps ranks to make the main line an alternative.

    Args:
        variation_id: Variation ID to demote
        target_rank: Target rank (must be > 0)
        actor_id: User ID performing demotion
        expected_version: Expected version for optimistic locking (optional)
    """

    variation_id: str
    target_rank: int
    actor_id: str
    expected_version: int | None = None


@dataclass
class ReorderVariationsCommand:
    """
    Command to reorder sibling variations.

    Args:
        parent_id: Parent move ID (None for root moves)
        chapter_id: Chapter ID
        new_order: List of variation IDs in desired order
        actor_id: User ID performing reorder
    """

    parent_id: str | None
    chapter_id: str
    new_order: list[str]
    actor_id: str


@dataclass
class PinVariationCommand:
    """
    Command to pin a variation (prevent auto-reordering).

    Args:
        variation_id: Variation ID to pin
        actor_id: User ID performing pin
    """

    variation_id: str
    actor_id: str


@dataclass
class UnpinVariationCommand:
    """
    Command to unpin a variation (allow auto-reordering).

    Args:
        variation_id: Variation ID to unpin
        actor_id: User ID performing unpin
    """

    variation_id: str
    actor_id: str


@dataclass
class SetVariationPriorityCommand:
    """
    Command to set variation priority.

    Args:
        variation_id: Variation ID
        priority: New priority level
        actor_id: User ID performing change
    """

    variation_id: str
    priority: VariationPriority
    actor_id: str


@dataclass
class SetVariationVisibilityCommand:
    """
    Command to set variation visibility.

    Args:
        variation_id: Variation ID
        visibility: New visibility level
        actor_id: User ID performing change
    """

    variation_id: str
    visibility: VariationVisibility
    actor_id: str
