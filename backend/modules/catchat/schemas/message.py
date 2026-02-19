from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class MessageCreate(BaseModel):
    """Send a text message in a conversation."""
    content: str = Field(..., min_length=1, max_length=5000)


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    sender_id: str
    sender_name: Optional[str]  # None if user has no display name set
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}
