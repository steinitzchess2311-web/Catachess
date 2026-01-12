"""Push notification channel (推送通知,未来功能)."""
import logging

logger = logging.getLogger(__name__)


class PushChannel:
    """
    Push notification channel for mobile/web push notifications.

    This is a placeholder for future implementation.
    When implemented, this would use:
    - Firebase Cloud Messaging (FCM) for mobile
    - Web Push API for browser notifications
    - Apple Push Notification service (APNs) for iOS
    """

    def __init__(self) -> None:
        self.enabled = False

    async def send(
        self, user_id: str, title: str, body: str, data: dict | None = None
    ) -> bool:
        """
        Send a push notification.

        Args:
            user_id: Target user ID
            title: Notification title
            body: Notification body
            data: Additional data payload

        Returns:
            True if sent successfully, False otherwise
        """
        logger.info(
            f"Push notifications not implemented. Would send to user {user_id}: {title}"
        )
        return False

    async def send_batch(
        self, notifications: list[tuple[str, str, str, dict | None]]
    ) -> list[bool]:
        """Send multiple push notifications in batch."""
        return [False] * len(notifications)
