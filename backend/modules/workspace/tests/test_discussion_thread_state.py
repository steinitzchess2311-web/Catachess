"""
Discussion thread state tests.
"""

import pytest

from workspace.db.repos.discussion_thread_repo import DiscussionThreadRepository
from workspace.domain.models.discussion_thread import (
    CreateThreadCommand,
    ResolveThreadCommand,
    PinThreadCommand,
)
from workspace.domain.services.discussion.thread_service import ThreadService
from workspace.domain.services.discussion.thread_state_service import ThreadStateService


@pytest.mark.asyncio
async def test_resolve_and_pin_thread(session, event_bus):
    thread_repo = DiscussionThreadRepository(session)
    thread_service = ThreadService(session, thread_repo, event_bus)
    state_service = ThreadStateService(session, thread_repo, event_bus)

    thread = await thread_service.create_thread(
        CreateThreadCommand(
            target_id="study-1",
            target_type="study",
            author_id="user-1",
            title="State",
            content="Check",
            thread_type="question",
        )
    )

    thread = await state_service.resolve_thread(
        ResolveThreadCommand(
            thread_id=thread.id,
            actor_id="user-1",
            resolved=True,
            version=thread.version,
        )
    )
    assert thread.resolved is True

    thread = await state_service.pin_thread(
        PinThreadCommand(
            thread_id=thread.id,
            actor_id="user-1",
            pinned=True,
            version=thread.version,
        )
    )
    assert thread.pinned is True
