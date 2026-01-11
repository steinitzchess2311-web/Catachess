"""
Event repository for event stream operations.
"""

from typing import Sequence

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from workspace.db.tables.events import Event
from workspace.domain.models.event import EventQuery
from workspace.events.types import EventType


class EventRepository:
    """
    Repository for Event database operations.

    Handles event creation and querying.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize repository.

        Args:
            session: Database session
        """
        self.session = session

    async def create(self, event: Event) -> Event:
        """
        Create a new event.

        Args:
            event: Event to create

        Returns:
            Created event
        """
        self.session.add(event)
        await self.session.flush()
        return event

    async def get_by_id(self, event_id: str) -> Event | None:
        """
        Get event by ID.

        Args:
            event_id: Event ID

        Returns:
            Event or None
        """
        stmt = select(Event).where(Event.id == event_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def query_events(self, query: EventQuery) -> Sequence[Event]:
        """
        Query events with filters.

        Args:
            query: Query parameters

        Returns:
            List of events
        """
        conditions = []

        if query.target_id is not None:
            conditions.append(Event.target_id == query.target_id)

        if query.actor_id is not None:
            conditions.append(Event.actor_id == query.actor_id)

        if query.workspace_id is not None:
            conditions.append(Event.workspace_id == query.workspace_id)

        if query.event_type is not None:
            conditions.append(Event.type == query.event_type)

        if query.after_version is not None:
            conditions.append(Event.version > query.after_version)

        stmt = select(Event)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        # Order by creation time (newest first)
        stmt = stmt.order_by(desc(Event.created_at))

        # Apply pagination
        stmt = stmt.limit(query.limit).offset(query.offset)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_events_for_target(
        self, target_id: str, limit: int = 100, offset: int = 0
    ) -> Sequence[Event]:
        """
        Get events for a specific target.

        Args:
            target_id: Target object ID
            limit: Maximum results
            offset: Result offset

        Returns:
            List of events
        """
        query = EventQuery(target_id=target_id, limit=limit, offset=offset)
        return await self.query_events(query)

    async def get_events_for_actor(
        self, actor_id: str, limit: int = 100, offset: int = 0
    ) -> Sequence[Event]:
        """
        Get events for a specific actor.

        Args:
            actor_id: Actor user ID
            limit: Maximum results
            offset: Result offset

        Returns:
            List of events
        """
        query = EventQuery(actor_id=actor_id, limit=limit, offset=offset)
        return await self.query_events(query)

    async def get_events_for_workspace(
        self, workspace_id: str, limit: int = 100, offset: int = 0
    ) -> Sequence[Event]:
        """
        Get events for a specific workspace.

        Args:
            workspace_id: Workspace ID
            limit: Maximum results
            offset: Result offset

        Returns:
            List of events
        """
        query = EventQuery(workspace_id=workspace_id, limit=limit, offset=offset)
        return await self.query_events(query)

    async def get_latest_version(self, target_id: str) -> int:
        """
        Get latest version number for a target.

        Args:
            target_id: Target object ID

        Returns:
            Latest version number (0 if no events)
        """
        from sqlalchemy import func as sqlfunc

        stmt = select(sqlfunc.max(Event.version)).where(Event.target_id == target_id)
        result = await self.session.execute(stmt)
        version = result.scalar_one_or_none()
        return version or 0

    async def count_events(self, query: EventQuery) -> int:
        """
        Count events matching query.

        Args:
            query: Query parameters

        Returns:
            Event count
        """
        from sqlalchemy import func as sqlfunc

        conditions = []

        if query.target_id is not None:
            conditions.append(Event.target_id == query.target_id)

        if query.actor_id is not None:
            conditions.append(Event.actor_id == query.actor_id)

        if query.workspace_id is not None:
            conditions.append(Event.workspace_id == query.workspace_id)

        if query.event_type is not None:
            conditions.append(Event.type == query.event_type)

        stmt = select(sqlfunc.count(Event.id))

        if conditions:
            stmt = stmt.where(and_(*conditions))

        result = await self.session.execute(stmt)
        return result.scalar_one()
