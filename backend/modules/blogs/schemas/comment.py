"""
Comment Pydantic Schemas
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


# ── Requests ──────────────────────────────────────────────────────────────────

class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)
    parent_id: Optional[UUID] = None
    quote_id: Optional[UUID] = None


class CommentEdit(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)
    version: int = Field(..., ge=1)


# ── Response ──────────────────────────────────────────────────────────────────

class CommentResponse(BaseModel):
    """
    Flat comment row returned by the API.
    Frontend builds the tree from parent_id.

    When is_deleted=True, content/author fields are still returned as-is
    so the frontend can decide how to render the placeholder.
    """
    id: UUID
    article_id: UUID
    parent_id: Optional[UUID]
    quote_id: Optional[UUID]

    author_id: UUID
    author_name: str

    content: str
    is_deleted: bool
    edited: bool

    like_count: int
    is_liked: bool = False

    version: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CommentListResponse(BaseModel):
    items: List[CommentResponse]
    total: int
