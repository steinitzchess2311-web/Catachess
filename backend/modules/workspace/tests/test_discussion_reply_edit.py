"""
Discussion reply edit/delete tests.
"""

import pytest

from workspace.db.repos.discussion_reply_repo import DiscussionReplyRepository
from workspace.db.repos.discussion_thread_repo import DiscussionThreadRepository
from workspace.domain.models.discussion_reply import AddReplyCommand, EditReplyCommand, DeleteReplyCommand
from workspace.domain.models.discussion_thread import CreateThreadCommand
from workspace.domain.services.discussion.reply_service import ReplyService
from workspace.domain.services.discussion.thread_service import ThreadService


@pytest.mark.asyncio
async def test_edit_and_delete_reply(session, event_bus):
    thread_repo = DiscussionThreadRepository(session)
    reply_repo = DiscussionReplyRepository(session)
    thread_service = ThreadService(session, thread_repo, event_bus)
    reply_service = ReplyService(session, reply_repo, thread_repo, event_bus)

    thread = await thread_service.create_thread(
        CreateThreadCommand(
            target_id="study-1",
            target_type="study",
            author_id="user-1",
            title="Edit",
            content="Root",
            thread_type="note",
        )
    )
    reply = await reply_service.add_reply(
        AddReplyCommand(
            thread_id=thread.id,
            author_id="user-1",
            content="First",
        )
    )
    reply = await reply_service.edit_reply(
        EditReplyCommand(
            reply_id=reply.id,
            content="Updated",
            actor_id="user-1",
            version=reply.version,
        )
    )
    assert reply.edited is True

    await reply_service.delete_reply(
        DeleteReplyCommand(reply_id=reply.id, actor_id="user-1")
    )
    assert await reply_repo.get_by_id(reply.id) is None
