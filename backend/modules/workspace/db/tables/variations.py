"""
Variation and move annotation table definitions.

Variations represent the move tree structure in a chess study chapter.
Move annotations are the analytical comments attached to specific moves.
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from workspace.db.base import Base, TimestampMixin


class VariationPriority(str, Enum):
    """
    Priority levels for variations.

    - MAIN: Main variation (the primary line)
    - ALTERNATIVE: Alternative variation (secondary lines)
    - DRAFT: Draft variation (work in progress, not published)
    """

    MAIN = "main"
    ALTERNATIVE = "alternative"
    DRAFT = "draft"


class VariationVisibility(str, Enum):
    """
    Visibility settings for variations.

    - PUBLIC: Visible to all viewers
    - MEMBERS: Visible to collaborators only
    - PRIVATE: Visible to owner only
    """

    PUBLIC = "public"
    MEMBERS = "members"
    PRIVATE = "private"


class Variation(Base, TimestampMixin):
    """
    Variation table - represents nodes in the chess move tree.

    Structure:
    - Each move is a node in the tree
    - parent_id points to the previous move
    - next_id points to the next move in the main line
    - rank determines the order among siblings (0=main, 1=first alternative, etc.)
    - chapter_id groups all moves belonging to one game

    Example tree structure:
    ```
    1. e4 (rank=0) -> 1...e5 (rank=0) -> 2. Nf3 (rank=0)
                   -> 1...c5 (rank=1)    [Sicilian variation]
                   -> 1...e6 (rank=2)    [French variation]
    ```
    """

    __tablename__ = "variations"

    # Primary key
    id: Mapped[str] = mapped_column(String(64), primary_key=True)

    # Chapter reference
    chapter_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("chapters.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Tree structure
    parent_id: Mapped[str | None] = mapped_column(
        String(64),
        ForeignKey("variations.id", ondelete="CASCADE"),
        nullable=True,  # NULL for root (starting position)
    )

    next_id: Mapped[str | None] = mapped_column(
        String(64),
        ForeignKey("variations.id", ondelete="SET NULL"),
        nullable=True,  # NULL for leaf nodes
    )

    # Move data
    move_number: Mapped[int] = mapped_column(Integer, nullable=False)
    """Full move number (e.g., 1, 2, 3...)"""

    color: Mapped[str] = mapped_column(String(5), nullable=False)
    """'white' or 'black'"""

    san: Mapped[str] = mapped_column(String(20), nullable=False)
    """Standard Algebraic Notation (e.g., 'e4', 'Nf3', 'O-O')"""

    uci: Mapped[str] = mapped_column(String(10), nullable=False)
    """Universal Chess Interface notation (e.g., 'e2e4', 'g1f3')"""

    fen: Mapped[str] = mapped_column(String(100), nullable=False)
    """FEN position after this move"""

    # Variation metadata
    rank: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    """
    Rank among sibling variations:
    - 0: Main variation
    - 1: First alternative
    - 2: Second alternative, etc.
    """

    priority: Mapped[VariationPriority] = mapped_column(
        String(20),
        nullable=False,
        default=VariationPriority.MAIN,
    )

    visibility: Mapped[VariationVisibility] = mapped_column(
        String(20),
        nullable=False,
        default=VariationVisibility.PUBLIC,
    )

    pinned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    """If true, this variation is pinned and won't be auto-reordered"""

    # Metadata
    created_by: Mapped[str] = mapped_column(String(64), nullable=False)
    """User ID who added this variation"""

    # Version tracking
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    """Incremented on each edit for optimistic locking"""

    # Indexes
    __table_args__ = (
        Index("ix_variations_chapter_id", "chapter_id"),
        Index("ix_variations_parent_id", "parent_id"),
        Index("ix_variations_chapter_parent_rank", "chapter_id", "parent_id", "rank"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Variation(id={self.id}, san={self.san}, rank={self.rank})>"


class MoveAnnotation(Base, TimestampMixin):
    """
    Move annotation table - analytical comments on specific moves.

    This is DISTINCT from discussions:
    - Move annotations are part of the chess analysis (exported with PGN)
    - Discussions are collaborative comments (NOT exported with PGN)

    Annotations include:
    - NAG symbols (!, ?, !!, ?!, !?, ??)
    - Text analysis
    - Author attribution

    Permissions:
    - Requires 'editor' permission to create/edit
    - Visible to all who can view the chapter
    """

    __tablename__ = "move_annotations"

    # Primary key
    id: Mapped[str] = mapped_column(String(64), primary_key=True)

    # Move reference
    move_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("variations.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Annotation content
    nag: Mapped[str | None] = mapped_column(String(10), nullable=True)
    """
    Numeric Annotation Glyph (NAG):
    - '!': Good move
    - '?': Mistake
    - '!!': Brilliant move
    - '??': Blunder
    - '!?': Interesting move
    - '?!': Dubious move
    """

    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    """Text analysis of the move"""

    # Attribution
    author_id: Mapped[str] = mapped_column(String(64), nullable=False)
    """User ID who wrote this annotation"""

    # Version tracking
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    """Incremented on each edit for optimistic locking"""

    # Indexes
    __table_args__ = (
        Index("ix_move_annotations_move_id", "move_id"),
        Index("ix_move_annotations_author_id", "author_id"),
    )

    def __repr__(self) -> str:
        """String representation."""
        nag_str = f" {self.nag}" if self.nag else ""
        return f"<MoveAnnotation(id={self.id}, move_id={self.move_id}{nag_str})>"
