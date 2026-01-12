"""
Discussion thread service.
"""

from ulid import ULID
from sqlalchemy.ext.asyncio import AsyncSession

from workspace.db.repos.discussion_thread_repo import DiscussionThreadRepository
from workspace.db.tables.discussion_threads import DiscussionThread, ThreadType
from workspace.domain.models.discussion_thread import (
    CreateThreadCommand,
    UpdateThreadCommand,
)
from workspace.domain.services.discussion.thread_events import publish_thread_event
from workspace.events.bus import EventBus
from workspace.events.types import EventType


class ThreadNotFoundError(Exception):
    pass


class OptimisticLockError(Exception):
    pass


class ThreadService:
    """Service for discussion threads."""

    def __init__(
        self,
        session: AsyncSession,
        thread_repo: DiscussionThreadRepository,
        event_bus: EventBus,
    ) -> None:
        self.session = session
        self.thread_repo = thread_repo
        self.event_bus = event_bus

    async def create_thread(self, command: CreateThreadCommand) -> DiscussionThread:
        thread = DiscussionThread(
            id=str(ULID()),
            target_id=command.target_id,
            target_type=command.target_type,
            author_id=command.author_id,
            title=command.title,
            content=command.content,
            thread_type=ThreadType(command.thread_type),
            pinned=False,
            resolved=False,
            version=1,
        )
        await self.thread_repo.create(thread)
        await publish_thread_event(
            self.event_bus,
            EventType.DISCUSSION_THREAD_CREATED,
            thread,
            command.author_id,
        )
        await self.session.commit()
        self.session.expunge(thread)
        return thread

    async def update_thread(self, command: UpdateThreadCommand) -> DiscussionThread:
        thread = await self._get_thread(command.thread_id)
        if thread.version != command.version:
            raise OptimisticLockError("Version conflict")
        thread.title = command.title
        thread.content = command.content
        thread.version += 1
        await self.thread_repo.update(thread)
        await publish_thread_event(
            self.event_bus,
            EventType.DISCUSSION_THREAD_UPDATED,
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
