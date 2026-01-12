"""Notification aggregator for batching and digest emails."""
from collections import defaultdict
from datetime import UTC, datetime, timedelta

from workspace.db.repos.notification_repo import NotificationRepository


class NotificationAggregator:
    """
    Aggregates notifications for digest emails.

    Supports:
    - Hourly digests
    - Daily digests
    - Weekly digests
    """

    def __init__(self, notification_repo: NotificationRepository) -> None:
        self.notification_repo = notification_repo

    async def get_digest_notifications(
        self, user_id: str, frequency: str = "daily"
    ) -> dict[str, list]:
        """
        Get notifications for digest email.

        Args:
            user_id: User ID
            frequency: Digest frequency (hourly/daily/weekly)

        Returns:
            Dict of event_type -> list of notifications
        """
        # Calculate time window based on frequency
        since = self._get_digest_window(frequency)

        # Get unread notifications since time window
        notifications = await self.notification_repo.get_unread_since(user_id, since)

        # Group by event type
        grouped = defaultdict(list)
        for notif in notifications:
            grouped[notif.event_type].append(notif)

        return dict(grouped)

    def _get_digest_window(self, frequency: str) -> datetime:
        """
        Get time window for digest based on frequency.

        Args:
            frequency: Digest frequency

        Returns:
            Datetime of window start
        """
        now = datetime.now(UTC)

        if frequency == "hourly":
            return now - timedelta(hours=1)
        elif frequency == "daily":
            return now - timedelta(days=1)
        elif frequency == "weekly":
            return now - timedelta(weeks=1)
        else:
            return now - timedelta(days=1)  # Default to daily

    def format_digest_summary(self, grouped_notifications: dict[str, list]) -> str:
        """
        Format notification digest into human-readable summary.

        Args:
            grouped_notifications: Dict of event_type -> list of notifications

        Returns:
            Formatted summary text
        """
        if not grouped_notifications:
            return "No new notifications"

        lines = []
        total = sum(len(notifs) for notifs in grouped_notifications.values())

        lines.append(f"You have {total} new notification(s):\n")

        for event_type, notifications in grouped_notifications.items():
            count = len(notifications)
            lines.append(f"  - {count} {event_type} notification(s)")

        return "\n".join(lines)

    async def mark_digest_sent(self, user_id: str, notification_ids: list[str]) -> None:
        """
        Mark notifications as included in digest.

        Args:
            user_id: User ID
            notification_ids: List of notification IDs included in digest
        """
        # For now, we could add a "digest_sent_at" field to notifications
        # Or just leave them as unread until user reads them in-app
        pass
