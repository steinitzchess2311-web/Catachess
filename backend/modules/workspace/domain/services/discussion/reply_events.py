"""
Discussion reply event helpers.
"""

from workspace.db.tables.discussion_replies import DiscussionReply
from workspace.domain.models.event import CreateEventCommand
from workspace.domain.services.discussion_mentions import extract_mentions
from workspace.events.bus import EventBus
from workspace.events.types import EventType


async def publish_reply_event(
    event_bus: EventBus,
    event_type: EventType,
    reply: DiscussionReply,
    actor_id: str,
) -> None:
    command = CreateEventCommand(
        type=event_type,
        actor_id=actor_id,
        target_id=reply.id,
        target_type="discussion_reply",
        version=reply.version,
        payload={"thread_id": reply.thread_id},
    )
    await event_bus.publish(command)


async def publish_reply_mentions(
    event_bus: EventBus, actor_id: str, reply_id: str, content: str
) -> None:
    for mention in extract_mentions(content):
        command = CreateEventCommand(
            type=EventType.DISCUSSION_MENTION,
            actor_id=actor_id,
            target_id=reply_id,
            target_type="discussion_reply",
            version=1,
            payload={"mentioned_user": mention},
        )
        await event_bus.publish(command)
