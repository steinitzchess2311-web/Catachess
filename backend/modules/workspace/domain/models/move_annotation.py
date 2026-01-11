"""
Move annotation domain model.

Move annotations are analytical comments attached to specific moves.
This is DISTINCT from discussions (collaborative comments).
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class MoveAnnotationModel:
    """
    Move annotation domain model.

    Represents an analytical comment on a move (part of chess analysis).
    """

    id: str
    move_id: str
    nag: str | None  # Numeric Annotation Glyph (!, ?, !!, ??, !?, ?!)
    text: str | None  # Text analysis
    author_id: str
    version: int
    created_at: datetime
    updated_at: datetime

    @property
    def has_nag(self) -> bool:
        """Check if annotation has NAG symbol."""
        return self.nag is not None

    @property
    def has_text(self) -> bool:
        """Check if annotation has text."""
        return self.text is not None and self.text.strip() != ""

    @property
    def is_empty(self) -> bool:
        """Check if annotation is empty (no NAG and no text)."""
        return not self.has_nag and not self.has_text


@dataclass
class AddMoveAnnotationCommand:
    """
    Command to add annotation to a move.

    Requires 'editor' permission.

    Args:
        move_id: Variation ID to annotate
        nag: Optional NAG symbol (!, ?, !!, ??, !?, ?!)
        text: Optional text analysis
        author_id: User ID adding annotation
    """

    move_id: str
    author_id: str
    nag: str | None = None
    text: str | None = None

    def __post_init__(self) -> None:
        """Validate that at least one of NAG or text is provided."""
        if self.nag is None and (self.text is None or self.text.strip() == ""):
            raise ValueError("Annotation must have either NAG or text")


@dataclass
class UpdateMoveAnnotationCommand:
    """
    Command to update move annotation.

    Increments version for optimistic locking.

    Args:
        annotation_id: Annotation ID to update
        nag: Optional new NAG symbol
        text: Optional new text
        version: Current version (for optimistic locking)
        actor_id: User ID performing update
    """

    annotation_id: str
    version: int
    actor_id: str
    nag: str | None = None
    text: str | None = None

    def __post_init__(self) -> None:
        """Validate that at least one of NAG or text is provided."""
        if self.nag is None and (self.text is None or self.text.strip() == ""):
            raise ValueError("Annotation must have either NAG or text")


@dataclass
class DeleteMoveAnnotationCommand:
    """
    Command to delete move annotation.

    Requires 'editor' permission.

    Args:
        annotation_id: Annotation ID to delete
        actor_id: User ID performing deletion
    """

    annotation_id: str
    actor_id: str


@dataclass
class SetNAGCommand:
    """
    Command to set NAG symbol on a move.

    Convenience command for setting only NAG.

    Args:
        move_id: Variation ID
        nag: NAG symbol (!, ?, !!, ??, !?, ?!)
        actor_id: User ID performing operation
    """

    move_id: str
    nag: str
    actor_id: str

    def __post_init__(self) -> None:
        """Validate NAG symbol."""
        valid_nags = {"!", "?", "!!", "??", "!?", "?!"}
        if self.nag not in valid_nags:
            raise ValueError(f"Invalid NAG symbol: {self.nag}")


@dataclass
class RemoveNAGCommand:
    """
    Command to remove NAG symbol from a move.

    Args:
        move_id: Variation ID
        actor_id: User ID performing operation
    """

    move_id: str
    actor_id: str
