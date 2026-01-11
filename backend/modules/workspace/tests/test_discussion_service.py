"""
Discussion service smoke tests.
"""

import pytest

from workspace.db.repos.discussion_reaction_repo import DiscussionReactionRepository
from workspace.db.repos.discussion_reply_repo import DiscussionReplyRepository
from workspace.db.repos.discussion_thread_repo import DiscussionThreadRepository
from workspace.domain.models.discussion_reaction import AddReactionCommand
from workspace.domain.models.discussion_reply import AddReplyCommand
from workspace.domain.models.discussion_thread import CreateThreadCommand
from workspace.domain.services.discussion.reaction_service import ReactionService
from workspace.domain.services.discussion.reply_service import ReplyService
from workspace.domain.services.discussion.thread_service import ThreadService


@pytest.mark.asyncio
async def test_thread_reply_reaction_flow(session, event_bus):
    thread_repo = DiscussionThreadRepository(session)
    reply_repo = DiscussionReplyRepository(session)
    reaction_repo = DiscussionReactionRepository(session)
    thread_service = ThreadService(session, thread_repo, event_bus)
    reply_service = ReplyService(session, reply_repo, thread_repo, event_bus)
    reaction_service = ReactionService(
        session, reaction_repo, thread_repo, reply_repo, event_bus
    )

    thread = await thread_service.create_thread(
        CreateThreadCommand(
            target_id="study-1",
            target_type="study",
            author_id="user-1",
            title="Opening question",
            content="What about 1.e4?",
            thread_type="question",
        )
    )
    reply = await reply_service.add_reply(
        AddReplyCommand(
            thread_id=thread.id,
            author_id="user-2",
            content="Try 1...c5",
        )
    )
    reaction = await reaction_service.add_reaction(
        AddReactionCommand(
            target_id=reply.id,
            target_type="reply",
            user_id="user-3",
            emoji="👍",
        )
    )

    assert thread.id
    assert reply.thread_id == thread.id
    assert reaction.target_id == reply.id
