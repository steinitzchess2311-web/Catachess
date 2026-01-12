"""
Event payload schema tests.
"""

import pytest

from workspace.domain.models.event import CreateEventCommand
from workspace.events.types import EventType


@pytest.mark.asyncio
async def test_event_payload_envelope(event_bus):
    command = CreateEventCommand(
        type=EventType.DISCUSSION_THREAD_CREATED,
        actor_id="user-1",
        target_id="thread-1",
        target_type="discussion_thread",
        version=1,
        payload={"title": "Hello"},
    )
    event = await event_bus.publish(command)

    payload = event.payload
    assert payload["event_type"] == str(EventType.DISCUSSION_THREAD_CREATED)
    assert payload["actor_id"] == "user-1"
    assert payload["target_id"] == "thread-1"
    assert payload["version"] == 1
    assert payload["payload"]["title"] == "Hello"
    # Verify timestamp is serialized as string
    assert isinstance(payload["timestamp"], str)
