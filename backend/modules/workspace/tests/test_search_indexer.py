"""
Search indexer subscriber tests.
"""

import pytest

from workspace.db.repos.discussion_reply_repo import DiscussionReplyRepository
from workspace.db.repos.discussion_thread_repo import DiscussionThreadRepository
from workspace.db.repos.search_index_repo import SearchIndexRepository
from workspace.domain.models.discussion_reply import AddReplyCommand, DeleteReplyCommand
from workspace.domain.models.discussion_thread import CreateThreadCommand
from workspace.domain.services.discussion.reply_service import ReplyService
from workspace.domain.services.discussion.thread_service import ThreadService
from workspace.domain.services.discussion.thread_state_service import ThreadStateService
from workspace.events.subscribers.search_indexer import register_search_indexer


@pytest.mark.asyncio
async def test_search_indexer_adds_and_removes_entries(session, event_bus):
    thread_repo = DiscussionThreadRepository(session)
    reply_repo = DiscussionReplyRepository(session)
    search_repo = SearchIndexRepository(session)
    register_search_indexer(event_bus, thread_repo, reply_repo, search_repo)

    thread_service = ThreadService(session, thread_repo, event_bus)
    reply_service = ReplyService(session, reply_repo, thread_repo, event_bus)
    state_service = ThreadStateService(session, thread_repo, event_bus)

    thread = await thread_service.create_thread(
        CreateThreadCommand(
            target_id="study-1",
            target_type="study",
            author_id="user-1",
            title="Index me",
            content="Hello",
            thread_type="note",
        )
    )
    entry = await search_repo.get_by_target(thread.id, "discussion_thread")
    assert entry is not None

    reply = await reply_service.add_reply(
        AddReplyCommand(
            thread_id=thread.id,
            author_id="user-2",
            content="Reply",
        )
    )
    reply_entry = await search_repo.get_by_target(reply.id, "discussion_reply")
    assert reply_entry is not None

    await reply_service.delete_reply(
        DeleteReplyCommand(reply_id=reply.id, actor_id="user-2")
    )
    assert await search_repo.get_by_target(reply.id, "discussion_reply") is None

    await state_service.delete_thread(thread.id)
    assert await search_repo.get_by_target(thread.id, "discussion_thread") is None
