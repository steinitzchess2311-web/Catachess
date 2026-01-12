"""
Event payload schemas and helpers.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class EventEnvelope(BaseModel):
    """
    Standard event envelope format.

    All events published through the system follow this structure.
    """
    event_id: str = Field(..., description="Unique event identifier")
    event_type: str = Field(..., description="Event type (e.g., 'node.created')")
    actor_id: str = Field(..., description="User who triggered the event")
    target_id: str = Field(..., description="Target object ID")
    target_type: str | None = Field(None, description="Target object type")
    timestamp: datetime = Field(..., description="Event timestamp")
    version: int = Field(..., description="Object version after this event")
    payload: dict[str, Any] = Field(default_factory=dict, description="Event-specific data")
    correlation_id: str | None = Field(None, description="Correlation ID for tracing related events")
    causation_id: str | None = Field(None, description="ID of event that caused this event")


class EventTarget(BaseModel):
    """Event target information."""
    target_id: str
    target_type: str | None


def build_event_envelope(
    event_id: str,
    event_type: str,
    actor_id: str,
    target_id: str,
    target_type: str | None,
    timestamp: datetime,
    version: int,
    payload: dict[str, Any] | None,
    correlation_id: str | None = None,
    causation_id: str | None = None,
) -> dict[str, Any]:
    """
    Build a standard event envelope.

    Args:
        event_id: Unique event identifier
        event_type: Event type
        actor_id: User who triggered the event
        target_id: Target object ID
        target_type: Target object type
        timestamp: Event timestamp
        version: Object version
        payload: Event-specific data
        correlation_id: Optional correlation ID for tracing
        causation_id: Optional ID of causative event

    Returns:
        Event envelope as dictionary
    """
    envelope = EventEnvelope(
        event_id=event_id,
        event_type=event_type,
        actor_id=actor_id,
        target_id=target_id,
        target_type=target_type,
        timestamp=timestamp,
        version=version,
        payload=payload or {},
        correlation_id=correlation_id,
        causation_id=causation_id,
    )
    return envelope.model_dump(mode='json')


def extract_event_payload(event) -> dict[str, Any]:
    payload = getattr(event, "payload", None) or {}
    if isinstance(payload, dict) and "payload" in payload and "event_type" in payload:
        return payload.get("payload") or {}
    return payload
