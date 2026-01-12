"""
Event bus for publishing and subscribing to events.

Simplified implementation for Phase 1:
- Writes events to database
- Provides hook points for future enhancements (WebSocket, notifications)
"""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from workspace.db.tables.events import Event as EventTable
from workspace.domain.models.event import CreateEventCommand
from workspace.domain.models.types import NodeType
from workspace.events.payloads import build_event_envelope
from workspace.events.types import EventType


class EventBus:
    """
    Event publishing and subscription system.

    Phase 1: Simple database write
    Future: Add WebSocket broadcasting, notification triggers, etc.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize event bus.

        Args:
            session: Database session
        """
        self.session = session
        self._subscribers: list[callable] = []

    async def publish(
        self,
        command: CreateEventCommand,
        event_id: str | None = None
    ) -> EventTable:
        """
        Publish an event.

        Writes event to database and notifies subscribers.
        Supports idempotency: if event_id already exists, returns existing event.

        Args:
            command: Event creation command
            event_id: Optional event ID (for idempotency). If not provided, generates UUID.

        Returns:
            Created or existing event
        """
        # Generate or use provided event_id
        if event_id is None:
            event_id = str(uuid.uuid4())

        if self.session is not None:
            # Check if event already exists (idempotency)
            from sqlalchemy import select
            existing_result = await self.session.execute(
                select(EventTable).where(EventTable.id == event_id)
            )
            existing_event = existing_result.scalar_one_or_none()

            if existing_event is not None:
                # Event already exists, return it (idempotent behavior)
                return existing_event

        # Create event record
        timestamp = datetime.now(UTC)
        payload = build_event_envelope(
            event_id=event_id,
            event_type=str(command.type),
            actor_id=command.actor_id,
            target_id=command.target_id,
            target_type=(
                str(command.target_type) if command.target_type is not None else None
            ),
            timestamp=timestamp,
            version=command.version,
            payload=command.payload,
        )
        event = EventTable(
            id=event_id,
            type=command.type,
            actor_id=command.actor_id,
            target_id=command.target_id,
            target_type=command.target_type,
            version=command.version,
            payload=payload,
            workspace_id=command.workspace_id,
        )

        if self.session is not None:
            self.session.add(event)
            await self.session.flush()

        # Notify subscribers (for WebSocket, notifications, etc.)
        await self._notify_subscribers(event)

        return event

    async def get_events_for_target(
        self,
        target_id: str,
        target_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[EventTable]:
        """
        Get events for a target (optional target_type filter).

        Args:
            target_id: Target object ID
            target_type: Optional target type filter
            limit: Max results
            offset: Results offset

        Returns:
            List of events (newest first)
        """
        if self.session is None:
            return []

        from sqlalchemy import desc, select

        stmt = select(EventTable).where(EventTable.target_id == target_id)
        if target_type is not None:
            stmt = stmt.where(EventTable.target_type == target_type)
        stmt = stmt.order_by(desc(EventTable.created_at)).limit(limit).offset(offset)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def _notify_subscribers(self, event: EventTable) -> None:
        """
        Notify all registered subscribers about event.

        Args:
            event: Published event
        """
        for subscriber in self._subscribers:
            try:
                await subscriber(event)
            except Exception as e:
                # Log error but don't fail event publication
                print(f"Subscriber error: {e}")

    def subscribe(self, callback: callable) -> None:
        """
        Subscribe to events.

        Args:
            callback: Async function to call when events are published
        """
        self._subscribers.append(callback)

    def unsubscribe(self, callback: callable) -> None:
        """
        Unsubscribe from events.

        Args:
            callback: Callback to remove
        """
        if callback in self._subscribers:
            self._subscribers.remove(callback)


# Helper functions for common event types

async def publish_node_created(
    bus: EventBus,
    actor_id: str,
    node_id: str,
    node_type: NodeType,
    parent_id: str | None,
    title: str,
    workspace_id: str | None,
) -> EventTable:
    """Publish node created event."""
    event_type_map = {
        NodeType.WORKSPACE: EventType.WORKSPACE_CREATED,
        NodeType.FOLDER: EventType.FOLDER_CREATED,
        NodeType.STUDY: EventType.STUDY_CREATED,
    }

    command = CreateEventCommand(
        type=event_type_map[node_type],
        actor_id=actor_id,
        target_id=node_id,
        target_type=node_type,
        version=1,
        payload={"parent_id": parent_id, "title": title},
        workspace_id=workspace_id,
    )

    return await bus.publish(command)


async def publish_node_updated(
    bus: EventBus,
    actor_id: str,
    node_id: str,
    node_type: NodeType,
    version: int,
    changes: dict[str, Any],
    workspace_id: str | None,
) -> EventTable:
    """Publish node updated event."""
    event_type_map = {
        NodeType.WORKSPACE: EventType.WORKSPACE_UPDATED,
        NodeType.FOLDER: EventType.FOLDER_RENAMED,  # Folder updates are renames
        NodeType.STUDY: EventType.STUDY_UPDATED,
    }

    command = CreateEventCommand(
        type=event_type_map[node_type],
        actor_id=actor_id,
        target_id=node_id,
        target_type=node_type,
        version=version,
        payload=changes,
        workspace_id=workspace_id,
    )

    return await bus.publish(command)


async def publish_node_moved(
    bus: EventBus,
    actor_id: str,
    node_id: str,
    node_type: NodeType,
    old_parent_id: str | None,
    new_parent_id: str | None,
    old_path: str,
    new_path: str,
    version: int,
    workspace_id: str | None,
) -> EventTable:
    """Publish node moved event."""
    event_type_map = {
        NodeType.WORKSPACE: EventType.WORKSPACE_MOVED,
        NodeType.FOLDER: EventType.FOLDER_MOVED,
        NodeType.STUDY: EventType.STUDY_MOVED,
    }

    command = CreateEventCommand(
        type=event_type_map[node_type],
        actor_id=actor_id,
        target_id=node_id,
        target_type=node_type,
        version=version,
        payload={
            "old_parent_id": old_parent_id,
            "new_parent_id": new_parent_id,
            "old_path": old_path,
            "new_path": new_path,
        },
        workspace_id=workspace_id,
    )

    return await bus.publish(command)


async def publish_node_deleted(
    bus: EventBus,
    actor_id: str,
    node_id: str,
    node_type: NodeType,
    version: int,
    workspace_id: str | None,
) -> EventTable:
    """Publish node soft-deleted event."""
    command = CreateEventCommand(
        type=EventType.NODE_SOFT_DELETED,
        actor_id=actor_id,
        target_id=node_id,
        target_type=node_type,
        version=version,
        payload={},
        workspace_id=workspace_id,
    )

    return await bus.publish(command)


async def publish_acl_shared(
    bus: EventBus,
    actor_id: str,
    object_id: str,
    user_id: str,
    permission: str,
    workspace_id: str | None,
) -> EventTable:
    """Publish ACL shared event."""
    command = CreateEventCommand(
        type=EventType.ACL_SHARED,
        actor_id=actor_id,
        target_id=object_id,
        target_type=None,
        version=1,
        payload={"user_id": user_id, "permission": permission},
        workspace_id=workspace_id,
    )

    return await bus.publish(command)


async def publish_acl_revoked(
    bus: EventBus,
    actor_id: str,
    object_id: str,
    user_id: str,
    workspace_id: str | None,
) -> EventTable:
    """Publish ACL revoked event."""
    command = CreateEventCommand(
        type=EventType.ACL_REVOKED,
        actor_id=actor_id,
        target_id=object_id,
        target_type=None,
        version=1,
        payload={"user_id": user_id},
        workspace_id=workspace_id,
    )

    return await bus.publish(command)


async def publish_study_created(
    bus: EventBus,
    actor_id: str,
    study_id: str,
    title: str,
    chapter_count: int,
    workspace_id: str | None,
) -> EventTable:
    """Publish study created event."""
    command = CreateEventCommand(
        type=EventType.STUDY_CREATED,
        actor_id=actor_id,
        target_id=study_id,
        target_type="study",
        version=1,
        payload={"title": title, "chapter_count": chapter_count},
        workspace_id=workspace_id,
    )

    return await bus.publish(command)


async def publish_chapter_imported(
    bus: EventBus,
    actor_id: str,
    study_id: str,
    chapter_id: str,
    title: str,
    order: int,
    r2_key: str,
    workspace_id: str | None,
) -> EventTable:
    """Publish chapter imported event."""
    command = CreateEventCommand(
        type=EventType.STUDY_CHAPTER_IMPORTED,
        actor_id=actor_id,
        target_id=chapter_id,
        target_type="chapter",
        version=1,
        payload={
            "study_id": study_id,
            "title": title,
            "order": order,
            "r2_key": r2_key,
        },
        workspace_id=workspace_id,
    )

    return await bus.publish(command)
