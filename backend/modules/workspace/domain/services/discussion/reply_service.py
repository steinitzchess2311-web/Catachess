"""Discussion reply service."""

from datetime import UTC, datetime
from ulid import ULID
from sqlalchemy.ext.asyncio import AsyncSession

from workspace.db.repos.discussion_reply_repo import DiscussionReplyRepository
from workspace.db.repos.discussion_thread_repo import DiscussionThreadRepository
from workspace.db.tables.discussion_replies import DiscussionReply
from workspace.domain.models.discussion_reply import AddReplyCommand, EditReplyCommand, DeleteReplyCommand
from workspace.domain.services.discussion.nesting import ensure_reply_depth
from workspace.domain.services.discussion.reply_events import publish_reply_event
from workspace.events.bus import EventBus
from workspace.events.types import EventType


class ReplyNotFoundError(Exception):
    pass


class OptimisticLockError(Exception):
    pass


class ReplyService:
    """Service for discussion replies."""

    def __init__(
        self,
        session: AsyncSession,
        reply_repo: DiscussionReplyRepository,
        thread_repo: DiscussionThreadRepository,
        event_bus: EventBus,
    ) -> None:
        self.session = session
        self.reply_repo = reply_repo
        self.thread_repo = thread_repo
        self.event_bus = event_bus

    async def add_reply(self, command: AddReplyCommand) -> DiscussionReply:
        thread = await self.thread_repo.get_by_id(command.thread_id)
        if not thread:
            raise ValueError("Thread not found")
        await ensure_reply_depth(self.reply_repo, command.parent_reply_id)
        reply = DiscussionReply(
            id=str(ULID()),
            thread_id=command.thread_id,
            parent_reply_id=command.parent_reply_id,
            quote_reply_id=command.quote_reply_id,
            author_id=command.author_id,
            content=command.content,
            edited=False,
            edit_history=[],
            version=1,
        )
        await self.reply_repo.create(reply)
        await publish_reply_event(
            self.event_bus, EventType.DISCUSSION_REPLY_ADDED, reply, command.author_id
        )
        await self.session.commit()
        self.session.expunge(reply)
        return reply

    async def edit_reply(self, command: EditReplyCommand) -> DiscussionReply:
        reply = await self._get_reply(command.reply_id)
        if reply.version != command.version:
            raise OptimisticLockError("Version conflict")
        entry = {
            "content": reply.content,
            "edited_at": datetime.now(UTC).isoformat(),
            "edited_by": command.actor_id,
        }
        reply.edit_history = (reply.edit_history + [entry])[-10:]
        reply.content = command.content
        reply.edited = True
        reply.version += 1
        await self.reply_repo.update(reply)
        await publish_reply_event(
            self.event_bus, EventType.DISCUSSION_REPLY_EDITED, reply, command.actor_id
        )
        await self.session.commit()
        return reply

    async def delete_reply(self, command: DeleteReplyCommand) -> None:
        reply = await self._get_reply(command.reply_id)
        await self.reply_repo.delete(reply)
        await publish_reply_event(
            self.event_bus, EventType.DISCUSSION_REPLY_DELETED, reply, command.actor_id
        )
        await self.session.commit()

    async def _get_reply(self, reply_id: str) -> DiscussionReply:
        reply = await self.reply_repo.get_by_id(reply_id)
        if not reply:
            raise ReplyNotFoundError(f"Reply {reply_id} not found")
        return reply
