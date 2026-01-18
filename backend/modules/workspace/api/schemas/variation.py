"""
Variation and move API schemas.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from modules.workspace.db.tables.variations import VariationPriority, VariationVisibility


class MoveCreate(BaseModel):
    """Schema for creating a move.

    Note: fen is optional - if not provided, the server will compute it
    from the parent position and UCI move.
    """

    parent_id: str | None = None
    san: str = Field(..., min_length=1, max_length=20, description="Standard Algebraic Notation")
    uci: str = Field(..., min_length=4, max_length=10, description="UCI notation")
    fen: str | None = Field(None, max_length=100, description="FEN after move (optional, computed server-side if not provided)")
    move_number: int = Field(..., ge=1, description="Move number")
    color: str = Field(..., pattern="^(white|black)$", description="white or black")
    rank: int = Field(default=0, ge=0, description="Rank (0=main line)")
    priority: VariationPriority = VariationPriority.MAIN
    visibility: VariationVisibility = VariationVisibility.PUBLIC


class MoveResponse(BaseModel):
    """Schema for move response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    chapter_id: str
    parent_id: str | None
    next_id: str | None
    move_number: int
    color: str
    san: str
    uci: str
    fen: str
    rank: int
    priority: VariationPriority
    visibility: VariationVisibility
    pinned: bool
    created_by: str
    version: int
    created_at: datetime
    updated_at: datetime


class MainlineMoveResponse(BaseModel):
    """Schema for mainline move list used by the study UI."""

    id: str
    move_number: int
    color: str
    san: str
    fen: str
    annotation_id: str | None
    annotation_text: str | None
    annotation_version: int | None


class MainlineMovesResponse(BaseModel):
    """Schema for mainline move list response."""

    moves: list[MainlineMoveResponse]


class PromoteVariationRequest(BaseModel):
    """Schema for promoting a variation."""

    expected_version: int | None = Field(None, description="Expected version for optimistic locking")


class DemoteVariationRequest(BaseModel):
    """Schema for demoting a variation."""

    target_rank: int = Field(..., ge=1, description="Target rank (must be > 0)")
    expected_version: int | None = Field(None, description="Expected version for optimistic locking")


class ReorderVariationsRequest(BaseModel):
    """Schema for reordering variations."""

    new_order: list[str] = Field(..., min_length=1, description="List of variation IDs in new order")
