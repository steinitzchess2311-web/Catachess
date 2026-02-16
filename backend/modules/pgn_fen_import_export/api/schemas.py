"""
API Schemas for FEN/PGN Import/Export

Pydantic models for request/response validation.
"""

from pydantic import BaseModel, field_validator
from typing import Optional

from ..services.fen_validator import validate_fen


class FenImportRequest(BaseModel):
    """Request body for FEN import."""

    study_id: str
    chapter_title: str
    fen: str

    @field_validator('fen')
    @classmethod
    def validate_fen_format(cls, v: str) -> str:
        """Validate FEN format using fen_validator."""
        result = validate_fen(v)
        if not result.valid:
            raise ValueError(result.error or "Invalid FEN string")
        # Return normalized FEN
        return result.normalized_fen or v

    @field_validator('chapter_title')
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Validate chapter title."""
        if not v or not v.strip():
            raise ValueError("Chapter title cannot be empty")
        if len(v) > 200:
            raise ValueError("Chapter title too long (max 200 characters)")
        return v.strip()

    @field_validator('study_id')
    @classmethod
    def validate_study_id(cls, v: str) -> str:
        """Validate study ID."""
        if not v or not v.strip():
            raise ValueError("Study ID cannot be empty")
        return v.strip()


class FenImportResponse(BaseModel):
    """Response for FEN import."""

    chapter_id: str
    starting_fen: Optional[str] = None  # NULL for standard position
    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "chapter_id": "abc123-def456-ghi789",
                "starting_fen": "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1",
                "message": "Chapter created successfully from FEN position"
            }
        }


class ErrorResponse(BaseModel):
    """Error response."""

    detail: str
    error_code: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Invalid FEN: must have at least 4 parts",
                "error_code": "INVALID_FEN"
            }
        }
