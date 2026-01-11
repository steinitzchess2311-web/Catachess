"""
Discussion thread schemas.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from workspace.api.schemas.markdown_validator import validate_markdown


class ThreadCreate(BaseModel):
    """Create discussion thread."""

    target_id: str = Field(..., min_length=1)
    target_type: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    thread_type: str = Field(..., min_length=1)

    @field_validator("content")
    @classmethod
    def _validate_content(cls, value: str) -> str:
        return validate_markdown(value)


class ThreadUpdate(BaseModel):
    """Update thread title/content."""

    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    version: int = Field(..., ge=1)

    @field_validator("content")
    @classmethod
    def _validate_content(cls, value: str) -> str:
        return validate_markdown(value)


class ThreadResolve(BaseModel):
    """Resolve or reopen thread."""

    resolved: bool
    version: int = Field(..., ge=1)


class ThreadPin(BaseModel):
    """Pin or unpin thread."""

    pinned: bool
    version: int = Field(..., ge=1)


class ThreadResponse(BaseModel):
    """Thread response model."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    target_id: str
    target_type: str
    author_id: str
    title: str
    content: str
    thread_type: str
    pinned: bool
    resolved: bool
    version: int
    created_at: datetime
    updated_at: datetime
