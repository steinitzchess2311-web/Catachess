"""
Discussion reply schemas.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from workspace.api.schemas.markdown_validator import validate_markdown


class ReplyCreate(BaseModel):
    """Create reply."""

    content: str = Field(..., min_length=1)
    parent_reply_id: str | None = None
    quote_reply_id: str | None = None

    @field_validator("content")
    @classmethod
    def _validate_content(cls, value: str) -> str:
        return validate_markdown(value)


class ReplyUpdate(BaseModel):
    """Update reply content."""

    content: str = Field(..., min_length=1)
    version: int = Field(..., ge=1)

    @field_validator("content")
    @classmethod
    def _validate_content(cls, value: str) -> str:
        return validate_markdown(value)


class ReplyResponse(BaseModel):
    """Reply response model."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    thread_id: str
    parent_reply_id: str | None
    quote_reply_id: str | None
    author_id: str
    content: str
    edited: bool
    edit_history: list[dict]
    version: int
    created_at: datetime
    updated_at: datetime
