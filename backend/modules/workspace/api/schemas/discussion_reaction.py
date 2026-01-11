"""
Discussion reaction schemas.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from workspace.domain.policies.limits import DiscussionLimits


class ReactionCreate(BaseModel):
    """Create reaction."""

    target_id: str = Field(..., min_length=1)
    target_type: str = Field(..., min_length=1)
    emoji: str = Field(..., min_length=1, max_length=16)

    @field_validator("emoji")
    @classmethod
    def _validate_emoji(cls, value: str) -> str:
        if value not in DiscussionLimits.ALLOWED_REACTION_EMOJIS:
            raise ValueError("Emoji is not allowed")
        return value


class ReactionResponse(BaseModel):
    """Reaction response model."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    target_id: str
    target_type: str
    user_id: str
    emoji: str
    created_at: datetime
    updated_at: datetime
