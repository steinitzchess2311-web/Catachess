"""
Discussion flow tests.
"""

import pytest

from workspace.db.repos.discussion_reaction_repo import DiscussionReactionRepository
from workspace.db.repos.discussion_reply_repo import DiscussionReplyRepository
from workspace.db.repos.discussion_thread_repo import DiscussionThreadRepository
from workspace.domain.models.discussion_reaction import AddReactionCommand
from workspace.domain.models.discussion_reply import AddReplyCommand
from workspace.domain.models.discussion_thread import CreateThreadCommand, ResolveThreadCommand
from workspace.domain.services.discussion.reaction_service import ReactionService
from workspace.domain.services.discussion.reply_service import ReplyService
from workspace.domain.services.discussion.thread_service import ThreadService
from workspace.domain.services.discussion.thread_state_service import ThreadStateService


@pytest.mark.asyncio
async def test_discussion_flow(session, event_bus):
    thread_repo = DiscussionThreadRepository(session)
    reply_repo = DiscussionReplyRepository(session)
    reaction_repo = DiscussionReactionRepository(session)
    thread_service = ThreadService(session, thread_repo, event_bus)
    reply_service = ReplyService(session, reply_repo, thread_repo, event_bus)
    reaction_service = ReactionService(
        session, reaction_repo, thread_repo, reply_repo, event_bus
    )
    state_service = ThreadStateService(session, thread_repo, event_bus)

    thread = await thread_service.create_thread(
        CreateThreadCommand(
            target_id="study-2",
            target_type="study",
            author_id="user-2",
            title="Flow",
            content="Question",
            thread_type="question",
        )
    )
    reply = await reply_service.add_reply(
        AddReplyCommand(
            thread_id=thread.id,
            author_id="user-3",
            content="Answer",
        )
    )
    reaction = await reaction_service.add_reaction(
        AddReactionCommand(
            target_id=reply.id,
            target_type="reply",
            user_id="user-4",
            emoji="❤️",
        )
    )
    thread = await state_service.resolve_thread(
        ResolveThreadCommand(
            thread_id=thread.id,
            actor_id="user-2",
            resolved=True,
            version=thread.version,
        )
    )
    assert reaction.target_id == reply.id
    assert thread.resolved is True
