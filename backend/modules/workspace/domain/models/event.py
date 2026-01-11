"""
Event domain model.

Represents events in the system's event stream.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from workspace.domain.models.types import NodeType
from workspace.events.types import EventType


@dataclass
class EventModel:
    """
    Domain model for Event.

    Events are immutable records of actions taken in the system.
    """

    id: str
    type: EventType
    actor_id: str
    target_id: str
    target_type: NodeType | None
    version: int
    payload: dict[str, Any]
    workspace_id: str | None
    created_at: datetime
    updated_at: datetime

    @property
    def is_node_event(self) -> bool:
        """Check if event is related to node operations."""
        node_events = {
            EventType.WORKSPACE_CREATED,
            EventType.WORKSPACE_UPDATED,
            EventType.WORKSPACE_DELETED,
            EventType.WORKSPACE_MOVED,
            EventType.FOLDER_CREATED,
            EventType.FOLDER_RENAMED,
            EventType.FOLDER_DELETED,
            EventType.FOLDER_MOVED,
            EventType.STUDY_CREATED,
            EventType.STUDY_UPDATED,
            EventType.STUDY_DELETED,
            EventType.STUDY_MOVED,
        }
        return self.type in node_events

    @property
    def is_acl_event(self) -> bool:
        """Check if event is related to ACL operations."""
        acl_events = {
            EventType.ACL_SHARED,
            EventType.ACL_REVOKED,
            EventType.ACL_ROLE_CHANGED,
            EventType.ACL_LINK_CREATED,
            EventType.ACL_LINK_REVOKED,
            EventType.ACL_INHERITED,
            EventType.ACL_INHERITANCE_BROKEN,
        }
        return self.type in acl_events


@dataclass
class CreateEventCommand:
    """Command to create an event."""

    type: EventType
    actor_id: str
    target_id: str
    target_type: NodeType | None
    version: int
    payload: dict[str, Any] = field(default_factory=dict)
    workspace_id: str | None = None


@dataclass
class EventQuery:
    """Query parameters for event stream."""

    target_id: str | None = None
    actor_id: str | None = None
    workspace_id: str | None = None
    event_type: EventType | None = None
    after_version: int | None = None
    limit: int = 100
    offset: int = 0
