"""
Presence API schemas.

Pydantic models for presence-related API requests and responses.
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from workspace.domain.models.types import PresenceStatus


class HeartbeatRequest(BaseModel):
    """Request schema for heartbeat updates."""

    study_id: str = Field(..., description="Study ID")
    chapter_id: str | None = Field(None, description="Current chapter ID")
    move_path: str | None = Field(None, description="Current move path")


class CursorPositionUpdate(BaseModel):
    """Request schema for updating cursor position."""

    chapter_id: str = Field(..., description="Chapter ID")
    move_path: str | None = Field(None, description="Move path (e.g., 'main.12.var2.3')")


class CursorPositionResponse(BaseModel):
    """Response schema for cursor position."""

    chapter_id: str
    move_path: str | None


class PresenceSessionResponse(BaseModel):
    """Response schema for presence session."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Session ID")
    user_id: str = Field(..., description="User ID")
    study_id: str = Field(..., description="Study ID")
    chapter_id: str | None = Field(None, description="Current chapter ID")
    move_path: str | None = Field(None, description="Current move path")
    status: PresenceStatus = Field(..., description="Presence status")
    last_heartbeat: datetime = Field(..., description="Last heartbeat timestamp")
    created_at: datetime = Field(..., description="Session creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    @property
    def cursor_position(self) -> CursorPositionResponse | None:
        """Get cursor position if available."""
        if self.chapter_id:
            return CursorPositionResponse(
                chapter_id=self.chapter_id,
                move_path=self.move_path
            )
        return None


class OnlineUserResponse(BaseModel):
    """Response schema for online user in a study."""

    user_id: str = Field(..., description="User ID")
    status: PresenceStatus = Field(..., description="Presence status")
    cursor_position: CursorPositionResponse | None = Field(
        None, description="Current cursor position"
    )
    last_heartbeat: datetime = Field(..., description="Last heartbeat timestamp")


class OnlineUsersResponse(BaseModel):
    """Response schema for list of online users."""

    study_id: str = Field(..., description="Study ID")
    users: list[OnlineUserResponse] = Field(..., description="List of online users")
    total: int = Field(..., description="Total number of online users")
