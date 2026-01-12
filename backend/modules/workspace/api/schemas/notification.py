"""Pydantic schemas for notification API."""
from datetime import datetime

from pydantic import BaseModel, Field


class NotificationBase(BaseModel):
    """Base notification schema."""

    type: str = Field(..., description="Notification type (event type)")
    title: str = Field(..., description="Notification title")
    body: str = Field(..., description="Notification body")
    target_id: str | None = Field(None, description="Target object ID")
    target_type: str | None = Field(None, description="Target object type")


class NotificationCreate(NotificationBase):
    """Schema for creating a notification."""

    user_id: str = Field(..., description="Target user ID")
    actor_id: str | None = Field(None, description="Actor user ID")
    data: dict = Field(default_factory=dict, description="Additional data")


class NotificationResponse(NotificationBase):
    """Schema for notification response."""

    id: str = Field(..., description="Notification ID")
    user_id: str = Field(..., description="Target user ID")
    actor_id: str | None = Field(None, description="Actor user ID")
    data: dict = Field(default_factory=dict, description="Additional data")
    read_at: datetime | None = Field(None, description="Read timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")

    model_config = {"from_attributes": True}


class NotificationListResponse(BaseModel):
    """Schema for notification list response."""

    notifications: list[NotificationResponse]
    total: int
    unread_count: int
    page: int
    page_size: int


class NotificationReadRequest(BaseModel):
    """Schema for marking notification(s) as read."""

    notification_ids: list[str] = Field(..., description="Notification IDs to mark as read")


class NotificationBulkReadRequest(BaseModel):
    """Schema for bulk read operations."""

    mark_all: bool = Field(False, description="Mark all notifications as read")
    before: datetime | None = Field(None, description="Mark all before this timestamp")


class NotificationPreferencesBase(BaseModel):
    """Base notification preferences schema."""

    preferences: dict[str, dict] = Field(
        default_factory=dict,
        description="Event-specific preferences {event_type: {enabled: bool, channels: [str]}}",
    )
    digest_frequency: str = Field(
        "instant", description="Digest frequency: instant, hourly, daily, weekly"
    )
    quiet_hours: dict = Field(
        default_factory=dict,
        description="Quiet hours config {enabled: bool, start_hour: int, end_hour: int}",
    )
    muted_objects: list[str] = Field(
        default_factory=list, description="List of muted object IDs"
    )
    enabled: bool = Field(True, description="Global notification enable/disable")


class NotificationPreferencesUpdate(NotificationPreferencesBase):
    """Schema for updating notification preferences."""

    pass


class NotificationPreferencesResponse(NotificationPreferencesBase):
    """Schema for notification preferences response."""

    id: str = Field(..., description="Preference record ID")
    user_id: str = Field(..., description="User ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {"from_attributes": True}


class NotificationTypeInfo(BaseModel):
    """Information about a notification type."""

    event_type: str = Field(..., description="Event type")
    enabled_by_default: bool = Field(..., description="Default enabled state")
    channels: list[str] = Field(..., description="Available channels")
    description: str = Field(..., description="User-friendly description")
    priority: str = Field(..., description="Priority level: high, medium, low")


class NotificationTypesResponse(BaseModel):
    """Schema for listing all notification types."""

    types: list[NotificationTypeInfo]
