from ulid import ULID

from workspace.db.repos.discussion_reaction_repo import DiscussionReactionRepository
from workspace.db.repos.discussion_reply_repo import DiscussionReplyRepository
from workspace.db.repos.discussion_thread_repo import DiscussionThreadRepository
from workspace.db.repos.notification_repo import NotificationRepository
from workspace.db.tables.notifications import Notification
from workspace.events.payloads import extract_event_payload
from workspace.events.types import EventType
from workspace.notifications.dispatcher import NotificationDispatcher


class NotificationCreator:
    def __init__(
        self,
        notification_repo: NotificationRepository,
        thread_repo: DiscussionThreadRepository,
        reply_repo: DiscussionReplyRepository,
        reaction_repo: DiscussionReactionRepository,
        dispatcher: NotificationDispatcher | None = None,
    ) -> None:
        self.notification_repo = notification_repo
        self.thread_repo = thread_repo
        self.reply_repo = reply_repo
        self.reaction_repo = reaction_repo
        self.dispatcher = dispatcher

    async def handle_event(self, event) -> None:
        payload = extract_event_payload(event)
        if event.type == EventType.DISCUSSION_MENTION:
            user_id = payload.get("mentioned_user_id")
            if user_id:
                await self._create_notification(user_id, event)
        if event.type == EventType.DISCUSSION_REPLY_ADDED:
            await self._notify_thread_author(event)
        if event.type == EventType.DISCUSSION_THREAD_RESOLVED:
            await self._notify_thread_author(event)
        if event.type == EventType.DISCUSSION_REACTION_ADDED:
            await self._notify_first_reaction(event)

    async def _notify_thread_author(self, event) -> None:
        target_id = event.target_id
        thread_id = target_id
        if event.type == EventType.DISCUSSION_REPLY_ADDED:
            reply = await self.reply_repo.get_by_id(target_id)
            if not reply:
                return
            thread_id = reply.thread_id
        thread = await self.thread_repo.get_by_id(thread_id)
        if not thread or thread.author_id == event.actor_id:
            return
        await self._create_notification(thread.author_id, event)

    async def _notify_first_reaction(self, event) -> None:
        reaction = await self.reaction_repo.get_by_id(event.target_id)
        if not reaction:
            return
        reactions = await self.reaction_repo.list_by_target(
            reaction.target_id, reaction.target_type
        )
        if len(reactions) != 1:
            return
        author_id = await self._get_target_author(reaction.target_id, reaction.target_type)
        if author_id and author_id != event.actor_id:
            await self._create_notification(author_id, event)

    async def _get_target_author(self, target_id: str, target_type: str) -> str | None:
        if target_type == "thread":
            thread = await self.thread_repo.get_by_id(target_id)
            return thread.author_id if thread else None
        reply = await self.reply_repo.get_by_id(target_id)
        return reply.author_id if reply else None

    async def _create_notification(self, user_id: str, event) -> None:
        payload = extract_event_payload(event)
        notification = Notification(
            id=str(ULID()),
            user_id=user_id,
            event_type=event.type,
            payload={
                "target_id": event.target_id,
                "target_type": event.target_type,
                "payload": payload,
            },
        )
        await self.notification_repo.create(notification)

        # Dispatch notification through channels if dispatcher is available
        if self.dispatcher:
            try:
                await self.dispatcher.dispatch(
                    user_id=user_id,
                    event_type=event.type,
                    payload={
                        "target_id": event.target_id,
                        "target_type": event.target_type,
                        "payload": payload,
                        "notification_id": notification.id,
                    },
                    target_id=event.target_id,
                )
            except Exception:
                # Don't fail notification creation if dispatch fails
                pass
