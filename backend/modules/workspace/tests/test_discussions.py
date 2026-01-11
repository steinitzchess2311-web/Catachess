"""
Discussion nesting tests.
"""

import pytest

from workspace.db.repos.discussion_reply_repo import DiscussionReplyRepository
from workspace.db.repos.discussion_thread_repo import DiscussionThreadRepository
from workspace.domain.models.discussion_reply import AddReplyCommand
from workspace.domain.models.discussion_thread import CreateThreadCommand
from workspace.domain.policies.limits import DiscussionLimits
from workspace.domain.services.discussion.reply_service import ReplyService
from workspace.domain.services.discussion.thread_service import ThreadService


@pytest.mark.asyncio
async def test_reply_nesting_limit(session, event_bus):
    thread_repo = DiscussionThreadRepository(session)
    reply_repo = DiscussionReplyRepository(session)
    thread_service = ThreadService(session, thread_repo, event_bus)
    reply_service = ReplyService(session, reply_repo, thread_repo, event_bus)

    thread = await thread_service.create_thread(
        CreateThreadCommand(
            target_id="study-1",
            target_type="study",
            author_id="user-1",
            title="Depth test",
            content="Root",
            thread_type="note",
        )
    )

    parent_id = None
    for _ in range(DiscussionLimits.MAX_REPLY_NESTING_LEVEL - 1):
        reply = await reply_service.add_reply(
            AddReplyCommand(
                thread_id=thread.id,
                author_id="user-1",
                content="Nested",
                parent_reply_id=parent_id,
            )
        )
        parent_id = reply.id

    with pytest.raises(ValueError):
        await reply_service.add_reply(
            AddReplyCommand(
                thread_id=thread.id,
                author_id="user-1",
                content="Too deep",
                parent_reply_id=parent_id,
            )
        )
