"""
Event table definition.

Events are the nervous system of the application, driving:
- Real-time WebSocket updates
- Notification creation
- Search indexing
- Activity logging
- Undo/redo
- Audit trails
"""

from typing import Any

from sqlalchemy import JSON, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from workspace.db.base import Base, TimestampMixin
from workspace.domain.models.types import NodeType
from workspace.events.types import EventType


class Event(Base, TimestampMixin):
    """
    Event log entry.

    Every write operation produces an event. Events are immutable once created.
    """

    __tablename__ = "events"

    # Primary key
    id: Mapped[str] = mapped_column(String(64), primary_key=True)

    # Event type (from EventType enum)
    type: Mapped[EventType] = mapped_column(String(100), nullable=False, index=True)

    # Actor (who performed the action)
    actor_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    # Target object
    target_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    target_type: Mapped[NodeType | None] = mapped_column(String(20), nullable=True)

    # Object version after this event
    # Used for optimistic locking and event ordering
    version: Mapped[int] = mapped_column(Integer, nullable=False)

    # Event payload (minimal diff or change description)
    # Structure depends on event type
    # Examples:
    # - node.created: {parent_id, title}
    # - node.moved: {old_parent_id, new_parent_id, old_path, new_path}
    # - acl.shared: {user_id, permission}
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    # Workspace context (for scoped subscriptions)
    # Events can be filtered by workspace for WebSocket subscriptions
    workspace_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    # Indexes
    __table_args__ = (
        # Fast event stream queries (by target, ordered by time)
        Index("ix_events_target_created", "target_id", "created_at"),
        # Fast actor activity queries
        Index("ix_events_actor_created", "actor_id", "created_at"),
        # Fast workspace event queries (for WebSocket subscriptions)
        Index("ix_events_workspace_created", "workspace_id", "created_at"),
        # Fast event type queries
        Index("ix_events_type_created", "type", "created_at"),
        # Version-based queries (for undo/redo)
        Index("ix_events_target_version", "target_id", "version"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<Event(id={self.id}, type={self.type}, "
            f"target={self.target_id}, version={self.version})>"
        )

    @property
    def event_type(self) -> str:
        """Compatibility accessor for tests expecting event_type."""
        return str(self.type)

    @property
    def is_node_event(self) -> bool:
        """Check if event is related to node operations."""
        return self.type in {
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

    @property
    def is_acl_event(self) -> bool:
        """Check if event is related to ACL operations."""
        return self.type in {
            EventType.ACL_SHARED,
            EventType.ACL_REVOKED,
            EventType.ACL_ROLE_CHANGED,
            EventType.ACL_LINK_CREATED,
            EventType.ACL_LINK_REVOKED,
            EventType.ACL_INHERITED,
            EventType.ACL_INHERITANCE_BROKEN,
        }

    @property
    def is_study_content_event(self) -> bool:
        """Check if event is related to study content."""
        return str(self.type).startswith("study.chapter.") or str(self.type).startswith(
            "study.move."
        )
