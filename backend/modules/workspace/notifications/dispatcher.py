"""Notification dispatcher that routes notifications to appropriate channels."""
from datetime import UTC, datetime

from workspace.db.repos.notification_preference_repo import NotificationPreferenceRepository
from workspace.notifications.channels.email import EmailChannel
from workspace.notifications.channels.in_app import InAppChannel
from workspace.notifications.channels.push import PushChannel


class NotificationDispatcher:
    """
    Dispatcher that routes notifications to channels based on user preferences.

    Checks:
    - User's notification preferences
    - Quiet hours
    - Muted objects
    - Channel-specific settings
    """

    def __init__(
        self,
        in_app_channel: InAppChannel,
        email_channel: EmailChannel | None = None,
        push_channel: PushChannel | None = None,
        preference_repo: NotificationPreferenceRepository | None = None,
    ) -> None:
        self.in_app_channel = in_app_channel
        self.email_channel = email_channel
        self.push_channel = push_channel
        self.preference_repo = preference_repo

    async def dispatch(
        self,
        user_id: str,
        event_type: str,
        payload: dict,
        target_id: str | None = None,
    ) -> dict[str, bool]:
        """
        Dispatch a notification to appropriate channels.

        Args:
            user_id: Target user ID
            event_type: Type of event
            payload: Notification payload
            target_id: Target object ID (for muting check)

        Returns:
            Dict of channel name -> success status
        """
        results = {}

        # Check if notifications are allowed
        if not await self._should_send_notification(user_id, event_type, target_id):
            return {"blocked": True}

        # Get user preferences
        channels = await self._get_enabled_channels(user_id, event_type)

        # Send to in-app channel (always enabled by default)
        if "in_app" in channels:
            try:
                await self.in_app_channel.send(user_id, event_type, payload)
                results["in_app"] = True
            except Exception as e:
                results["in_app"] = False
                results["in_app_error"] = str(e)

        # Send to email channel (if enabled)
        if "email" in channels and self.email_channel:
            # TODO: Format email using templates
            # For now, skip email sending
            results["email"] = False

        # Send to push channel (if enabled)
        if "push" in channels and self.push_channel:
            results["push"] = False

        return results

    async def _should_send_notification(
        self, user_id: str, event_type: str, target_id: str | None
    ) -> bool:
        """
        Check if notification should be sent based on preferences.

        Args:
            user_id: Target user ID
            event_type: Event type
            target_id: Target object ID

        Returns:
            True if notification should be sent
        """
        if not self.preference_repo:
            return True

        prefs = await self.preference_repo.get_by_user_id(user_id)
        if not prefs:
            return True

        # Check global enabled flag
        if not prefs.enabled:
            return False

        # Check muted objects
        if target_id and target_id in prefs.muted_objects:
            return False

        # Check quiet hours
        if await self._is_in_quiet_hours(prefs.quiet_hours):
            return False

        return True

    async def _is_in_quiet_hours(self, quiet_hours: dict) -> bool:
        """
        Check if current time is in user's quiet hours.

        Args:
            quiet_hours: Dict with enabled, start_hour, end_hour

        Returns:
            True if in quiet hours
        """
        if not quiet_hours.get("enabled"):
            return False

        now = datetime.now(UTC)
        current_hour = now.hour

        start = quiet_hours.get("start_hour", 22)  # Default 10 PM
        end = quiet_hours.get("end_hour", 8)  # Default 8 AM

        # Handle overnight quiet hours (e.g., 22:00 to 08:00)
        if start > end:
            return current_hour >= start or current_hour < end
        else:
            return start <= current_hour < end

    async def _get_enabled_channels(self, user_id: str, event_type: str) -> list[str]:
        """
        Get list of enabled channels for this user and event type.

        Args:
            user_id: User ID
            event_type: Event type

        Returns:
            List of enabled channel names
        """
        if not self.preference_repo:
            return ["in_app"]  # Default to in-app only

        prefs = await self.preference_repo.get_by_user_id(user_id)
        if not prefs:
            return ["in_app"]

        # Check event-specific preferences
        event_prefs = prefs.preferences.get(event_type, {})
        if not event_prefs.get("enabled", True):
            return []

        # Get channels for this event type
        channels = event_prefs.get("channels", ["in_app"])
        return channels
