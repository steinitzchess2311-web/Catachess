"""
Discussion thread event helpers.
"""

from workspace.db.tables.discussion_threads import DiscussionThread
from workspace.domain.models.event import CreateEventCommand
from workspace.domain.services.discussion_mentions import extract_mentions
from workspace.events.bus import EventBus
from workspace.events.types import EventType


async def publish_thread_event(
    event_bus: EventBus,
    event_type: EventType,
    thread: DiscussionThread,
    actor_id: str,
) -> None:
    command = CreateEventCommand(
        type=event_type,
        actor_id=actor_id,
        target_id=thread.id,
        target_type="discussion_thread",
        version=thread.version,
        payload={"target_id": thread.target_id, "target_type": thread.target_type},
    )
    await event_bus.publish(command)


async def publish_thread_mentions(
    event_bus: EventBus, actor_id: str, thread_id: str, content: str
) -> None:
    for mention in extract_mentions(content):
        command = CreateEventCommand(
            type=EventType.DISCUSSION_MENTION,
            actor_id=actor_id,
            target_id=thread_id,
            target_type="discussion_thread",
            version=1,
            payload={"mentioned_user": mention},
        )
        await event_bus.publish(command)
