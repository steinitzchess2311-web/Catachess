"""Notification rules defining which events trigger notifications."""
from workspace.events.types import EventType

# Map event types to notification settings
NOTIFICATION_RULES = {
    # Discussion events
    EventType.DISCUSSION_MENTION: {
        "enabled_by_default": True,
        "channels": ["in_app", "email"],
        "description": "When someone mentions you in a discussion",
        "priority": "high",
    },
    EventType.DISCUSSION_THREAD_CREATED: {
        "enabled_by_default": False,
        "channels": ["in_app"],
        "description": "When a new discussion thread is created",
        "priority": "low",
    },
    EventType.DISCUSSION_THREAD_ADDED: {
        "enabled_by_default": False,
        "channels": ["in_app"],
        "description": "When a new discussion thread is added",
        "priority": "low",
    },
    EventType.DISCUSSION_REPLY_ADDED: {
        "enabled_by_default": True,
        "channels": ["in_app"],
        "description": "When someone replies to your discussion",
        "priority": "medium",
    },
    EventType.DISCUSSION_THREAD_RESOLVED: {
        "enabled_by_default": True,
        "channels": ["in_app"],
        "description": "When your discussion thread is resolved",
        "priority": "low",
    },
    EventType.DISCUSSION_REACTION_ADDED: {
        "enabled_by_default": True,
        "channels": ["in_app"],
        "description": "When someone reacts to your discussion",
        "priority": "low",
    },
    # Share events
    "acl.permission.granted": {
        "enabled_by_default": True,
        "channels": ["in_app", "email"],
        "description": "When someone shares a study with you",
        "priority": "high",
    },
    "acl.permission.revoked": {
        "enabled_by_default": True,
        "channels": ["in_app"],
        "description": "When your access to a study is revoked",
        "priority": "medium",
    },
    # Study update events
    "study.chapter.added": {
        "enabled_by_default": False,
        "channels": ["in_app"],
        "description": "When a new chapter is added to a shared study",
        "priority": "low",
    },
    "study.move.added": {
        "enabled_by_default": False,
        "channels": ["in_app"],
        "description": "When moves are added to a shared study",
        "priority": "low",
    },
    "study.variation.added": {
        "enabled_by_default": False,
        "channels": ["in_app"],
        "description": "When a variation is added to a shared study",
        "priority": "low",
    },
    # Export events
    "pgn.export.completed": {
        "enabled_by_default": True,
        "channels": ["in_app", "email"],
        "description": "When your export is ready",
        "priority": "high",
    },
    "pgn.export.failed": {
        "enabled_by_default": True,
        "channels": ["in_app"],
        "description": "When your export fails",
        "priority": "high",
    },
}


def should_notify(event_type: str, user_preferences: dict | None = None) -> bool:
    """
    Check if an event should trigger a notification.

    Args:
        event_type: Event type
        user_preferences: User's notification preferences (optional)

    Returns:
        True if notification should be sent
    """
    rule = NOTIFICATION_RULES.get(event_type)
    if not rule:
        return False

    # If user has specific preferences, use those
    if user_preferences and event_type in user_preferences:
        return user_preferences[event_type].get("enabled", True)

    # Otherwise use default
    return rule["enabled_by_default"]


def get_default_channels(event_type: str) -> list[str]:
    """
    Get default notification channels for an event type.

    Args:
        event_type: Event type

    Returns:
        List of channel names
    """
    rule = NOTIFICATION_RULES.get(event_type)
    if not rule:
        return ["in_app"]

    return rule["channels"]


def get_notification_priority(event_type: str) -> str:
    """
    Get priority level for an event type.

    Args:
        event_type: Event type

    Returns:
        Priority level (high/medium/low)
    """
    rule = NOTIFICATION_RULES.get(event_type)
    if not rule:
        return "low"

    return rule.get("priority", "low")


def get_all_notification_types() -> dict[str, dict]:
    """
    Get all available notification types with their settings.

    Returns:
        Dict of event_type -> settings
    """
    return NOTIFICATION_RULES.copy()
