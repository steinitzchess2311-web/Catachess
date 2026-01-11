"""
Discussion mention event tests.
"""

import pytest

from workspace.db.repos.discussion_thread_repo import DiscussionThreadRepository
from workspace.db.repos.event_repo import EventRepository
from workspace.domain.models.discussion_thread import CreateThreadCommand
from workspace.domain.models.event import EventQuery
from workspace.domain.services.discussion.thread_service import ThreadService
from workspace.events.types import EventType


@pytest.mark.asyncio
async def test_mentions_emit_events(session, event_bus):
    thread_repo = DiscussionThreadRepository(session)
    thread_service = ThreadService(session, thread_repo, event_bus)

    await thread_service.create_thread(
        CreateThreadCommand(
            target_id="study-1",
            target_type="study",
            author_id="user-1",
            title="Mentions",
            content="Hello @user-2 and @user-3",
            thread_type="note",
        )
    )

    event_repo = EventRepository(session)
    events = await event_repo.query_events(
        EventQuery(event_type=EventType.DISCUSSION_MENTION)
    )
    assert len(events) == 2
