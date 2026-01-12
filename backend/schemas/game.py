"""
Game API Schemas

Pydantic models for game storage API endpoints.
"""
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ===== Request Schemas =====

class MoveRequest(BaseModel):
    """Move data from frontend"""
    from_square: dict[str, int]  # {"file": 0-7, "rank": 0-7}
    to_square: dict[str, int]
    promotion: Optional[str] = None  # "queen", "rook", "bishop", "knight"


class SaveMoveRequest(BaseModel):
    """Request to save a move"""
    game_id: str
    move: MoveRequest
    position_fen: str
    is_variation: bool = False
    parent_move_id: Optional[str] = None
    comment: Optional[str] = None
    nag: Optional[int] = None  # Numeric Annotation Glyph (1=!, 2=?, etc.)
    move_number: int


class StartVariationRequest(BaseModel):
    """Request to start a variation"""
    game_id: str
    parent_move_id: str


class EndVariationRequest(BaseModel):
    """Request to end current variation"""
    game_id: str


class AddCommentRequest(BaseModel):
    """Request to add comment to move"""
    game_id: str
    move_id: Optional[str] = None  # If None, adds to last move
    comment: str


class AddNAGRequest(BaseModel):
    """Request to add NAG annotation to move"""
    game_id: str
    move_id: Optional[str] = None  # If None, adds to last move
    nag: int  # 1=!, 2=?, 3=!!, 4=??, etc.


# ===== Response Schemas =====

class SaveMoveResponse(BaseModel):
    """Response after saving a move"""
    success: bool
    move_id: str
    pgn_preview: str = Field(..., description="Preview of PGN (first 100 chars)")


class VariationResponse(BaseModel):
    """Response for variation operations"""
    success: bool
    variation_id: Optional[str] = None


class CommentResponse(BaseModel):
    """Response for comment/NAG operations"""
    success: bool


class PGNResponse(BaseModel):
    """Response with full PGN data"""
    pgn: str
    game_id: str
    move_count: int


class GameInfoResponse(BaseModel):
    """Complete game information"""
    game_id: str
    pgn: str
    move_count: int
    current_position: str  # FEN
    player_white: Optional[str] = None
    player_black: Optional[str] = None
    result: str = "*"
    created_at: datetime
    updated_at: datetime


class DeleteGameResponse(BaseModel):
    """Response after deleting a game"""
    success: bool
    message: str = "Game deleted successfully"
