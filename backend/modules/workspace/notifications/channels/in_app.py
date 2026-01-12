"""In-app notification channel (站内通知)."""
from datetime import UTC, datetime

from ulid import ULID

from workspace.db.repos.notification_repo import NotificationRepository
from workspace.db.tables.notifications import Notification


class InAppChannel:
    """In-app notification channel that stores notifications in the database."""

    def __init__(self, notification_repo: NotificationRepository) -> None:
        self.notification_repo = notification_repo

    async def send(self, user_id: str, event_type: str, payload: dict) -> Notification:
        """
        Send an in-app notification.

        Args:
            user_id: Target user ID
            event_type: Type of event (e.g., "discussion.mention")
            payload: Notification payload (event data)

        Returns:
            Created Notification object
        """
        notification = Notification(
            id=str(ULID()),
            user_id=user_id,
            event_type=event_type,
            payload=payload,
            read_at=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        self.notification_repo.session.add(notification)
        await self.notification_repo.session.flush()
        return notification

    async def send_batch(
        self, notifications: list[tuple[str, str, dict]]
    ) -> list[Notification]:
        """
        Send multiple notifications in batch.

        Args:
            notifications: List of (user_id, event_type, payload) tuples

        Returns:
            List of created Notification objects
        """
        created = []
        for user_id, event_type, payload in notifications:
            notif = await self.send(user_id, event_type, payload)
            created.append(notif)
        return created
