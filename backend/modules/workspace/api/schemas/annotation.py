"""
Move annotation API schemas.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AnnotationCreate(BaseModel):
    """Schema for creating a move annotation."""

    nag: str | None = Field(None, max_length=10, description="NAG symbol (!, ?, !!, ??, !?, ?!)")
    text: str | None = Field(None, max_length=5000, description="Annotation text")

    @field_validator("nag")
    @classmethod
    def validate_nag(cls, v: str | None) -> str | None:
        """Validate NAG symbol."""
        if v is not None:
            valid_nags = ["!", "?", "!!", "??", "!?", "?!"]
            if v not in valid_nags:
                raise ValueError(f"Invalid NAG symbol. Must be one of: {', '.join(valid_nags)}")
        return v

    def model_post_init(self, __context):
        """Validate that at least one field is provided."""
        if self.nag is None and (self.text is None or self.text.strip() == ""):
            raise ValueError("Must provide either NAG or text")


class AnnotationUpdate(BaseModel):
    """Schema for updating a move annotation."""

    nag: str | None = Field(None, max_length=10, description="NAG symbol")
    text: str | None = Field(None, max_length=5000, description="Annotation text")
    version: int = Field(..., description="Current version for optimistic locking")

    @field_validator("nag")
    @classmethod
    def validate_nag(cls, v: str | None) -> str | None:
        """Validate NAG symbol."""
        if v is not None:
            valid_nags = ["!", "?", "!!", "??", "!?", "?!"]
            if v not in valid_nags:
                raise ValueError(f"Invalid NAG symbol. Must be one of: {', '.join(valid_nags)}")
        return v

    def model_post_init(self, __context):
        """Validate that at least one field is provided."""
        if self.nag is None and (self.text is None or self.text.strip() == ""):
            raise ValueError("Must provide either NAG or text")


class SetNAGRequest(BaseModel):
    """Schema for setting NAG symbol."""

    nag: str = Field(..., max_length=10, description="NAG symbol (!, ?, !!, ??, !?, ?!)")

    @field_validator("nag")
    @classmethod
    def validate_nag(cls, v: str) -> str:
        """Validate NAG symbol."""
        valid_nags = ["!", "?", "!!", "??", "!?", "?!"]
        if v not in valid_nags:
            raise ValueError(f"Invalid NAG symbol. Must be one of: {', '.join(valid_nags)}")
        return v


class AnnotationResponse(BaseModel):
    """Schema for annotation response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    move_id: str
    nag: str | None
    text: str | None
    author_id: str
    version: int
    created_at: datetime
    updated_at: datetime
