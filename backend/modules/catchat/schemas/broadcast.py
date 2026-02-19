from datetime import datetime
from pydantic import BaseModel, Field


class BroadcastCreate(BaseModel):
    """Send a broadcast to all users (admin only)."""
    content: str = Field(..., min_length=1, max_length=5000)


class BroadcastResponse(BaseModel):
    id: str
    sender_id: str
    sender_name: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}
