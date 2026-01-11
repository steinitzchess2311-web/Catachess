"""
Discussion thread state service.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from workspace.db.repos.discussion_thread_repo import DiscussionThreadRepository
from workspace.db.tables.discussion_threads import DiscussionThread
from workspace.domain.models.discussion_thread import ResolveThreadCommand, PinThreadCommand
from workspace.domain.services.discussion.thread_events import publish_thread_event
from workspace.events.bus import EventBus
from workspace.events.types import EventType


class ThreadNotFoundError(Exception):
    pass


class ThreadStateService:
    """Service for resolving/pinning/deleting threads."""

    def __init__(
        self,
        session: AsyncSession,
        thread_repo: DiscussionThreadRepository,
        event_bus: EventBus,
    ) -> None:
        self.session = session
        self.thread_repo = thread_repo
        self.event_bus = event_bus

    async def resolve_thread(self, command: ResolveThreadCommand) -> DiscussionThread:
        thread = await self._get_thread(command.thread_id)
        if thread.version != command.version:
            raise ValueError("Version conflict")
        thread.resolved = command.resolved
        thread.version += 1
        await self.thread_repo.update(thread)
        event = (
            EventType.DISCUSSION_THREAD_RESOLVED
            if command.resolved
            else EventType.DISCUSSION_THREAD_REOPENED
        )
        await publish_thread_event(self.event_bus, event, thread, command.actor_id)
        await self.session.commit()
        return thread

    async def pin_thread(self, command: PinThreadCommand) -> DiscussionThread:
        thread = await self._get_thread(command.thread_id)
        if thread.version != command.version:
            raise ValueError("Version conflict")
        thread.pinned = command.pinned
        thread.version += 1
        await self.thread_repo.update(thread)
        await publish_thread_event(
            self.event_bus,
            EventType.DISCUSSION_THREAD_PINNED,
            thread,
            command.actor_id,
        )
        await self.session.commit()
        return thread

    async def delete_thread(self, thread_id: str) -> None:
        thread = await self._get_thread(thread_id)
        await self.thread_repo.delete(thread)
        await publish_thread_event(
            self.event_bus, EventType.DISCUSSION_THREAD_DELETED, thread, thread.author_id
        )
        await self.session.commit()

    async def _get_thread(self, thread_id: str) -> DiscussionThread:
        thread = await self.thread_repo.get_by_id(thread_id)
        if not thread:
            raise ThreadNotFoundError(f"Thread {thread_id} not found")
        return thread
