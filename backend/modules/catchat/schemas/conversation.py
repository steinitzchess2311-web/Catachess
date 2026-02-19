from datetime import datetime
from pydantic import BaseModel


class ConversationCreate(BaseModel):
    """Open or retrieve an existing conversation with another user."""
    user_id: str  # UUID string of the other participant


class ConversationResponse(BaseModel):
    id: str
    other_user_id: str        # UUID of the other participant
    last_message_at: datetime  # use this to sort conversation list
    created_at: datetime

    model_config = {"from_attributes": True}
