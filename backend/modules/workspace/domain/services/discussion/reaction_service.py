"""
Discussion reaction service.
"""

from ulid import new as ulid_new
from sqlalchemy.ext.asyncio import AsyncSession

from workspace.db.repos.discussion_reaction_repo import DiscussionReactionRepository
from workspace.db.repos.discussion_reply_repo import DiscussionReplyRepository
from workspace.db.repos.discussion_thread_repo import DiscussionThreadRepository
from workspace.db.tables.discussion_reactions import DiscussionReaction
from workspace.domain.models.discussion_reaction import (
    AddReactionCommand,
    RemoveReactionCommand,
)
from workspace.domain.models.event import CreateEventCommand
from workspace.domain.policies.limits import DiscussionLimits
from workspace.events.bus import EventBus
from workspace.events.types import EventType


class ReactionNotFoundError(Exception):
    pass


class ReactionService:
    """Service for discussion reactions."""

    def __init__(
        self,
        session: AsyncSession,
        reaction_repo: DiscussionReactionRepository,
        thread_repo: DiscussionThreadRepository,
        reply_repo: DiscussionReplyRepository,
        event_bus: EventBus,
    ) -> None:
        self.session = session
        self.reaction_repo = reaction_repo
        self.thread_repo = thread_repo
        self.reply_repo = reply_repo
        self.event_bus = event_bus

    async def add_reaction(self, command: AddReactionCommand) -> DiscussionReaction:
        await self._ensure_target(command.target_id, command.target_type)
        reactions = await self.reaction_repo.list_by_target(
            command.target_id, command.target_type
        )
        if len(reactions) >= DiscussionLimits.MAX_REACTIONS_PER_COMMENT:
            raise ValueError("Reaction limit reached")
        reaction = DiscussionReaction(
            id=str(ulid_new()),
            target_id=command.target_id,
            target_type=command.target_type,
            user_id=command.user_id,
            emoji=command.emoji,
        )
        await self.reaction_repo.create(reaction)
        await self._publish_event(EventType.DISCUSSION_REACTION_ADDED, reaction)
        await self.session.commit()
        return reaction

    async def remove_reaction(self, command: RemoveReactionCommand) -> None:
        reaction = await self.reaction_repo.get_by_id(command.reaction_id)
        if not reaction:
            raise ReactionNotFoundError("Reaction not found")
        if reaction.user_id != command.user_id:
            raise ValueError("Only creator can remove reaction")
        await self.reaction_repo.delete(reaction)
        await self._publish_event(EventType.DISCUSSION_REACTION_REMOVED, reaction)
        await self.session.commit()

    async def _ensure_target(self, target_id: str, target_type: str) -> None:
        if target_type == "thread":
            thread = await self.thread_repo.get_by_id(target_id)
            if not thread:
                raise ValueError("Thread not found")
            return
        if target_type == "reply":
            reply = await self.reply_repo.get_by_id(target_id)
            if not reply:
                raise ValueError("Reply not found")
            return
        raise ValueError("Invalid reaction target type")

    async def _publish_event(
        self, event_type: EventType, reaction: DiscussionReaction
    ) -> None:
        command = CreateEventCommand(
            type=event_type,
            actor_id=reaction.user_id,
            target_id=reaction.id,
            target_type="discussion_reaction",
            version=1,
            payload={
                "target_id": reaction.target_id,
                "target_type": reaction.target_type,
                "emoji": reaction.emoji,
            },
        )
        await self.event_bus.publish(command)
