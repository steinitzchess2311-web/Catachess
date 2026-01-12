"""Tests for notification rules."""
import pytest

from workspace.domain.policies.notification_rules import (
    NOTIFICATION_RULES,
    get_all_notification_types,
    get_default_channels,
    get_notification_priority,
    should_notify,
)
from workspace.events.types import EventType


def test_notification_rules_defined() -> None:
    """Test that notification rules are properly defined."""
    assert len(NOTIFICATION_RULES) > 0

    # Check structure of each rule
    for event_type, rule in NOTIFICATION_RULES.items():
        assert "enabled_by_default" in rule
        assert "channels" in rule
        assert "description" in rule
        assert "priority" in rule
        assert isinstance(rule["enabled_by_default"], bool)
        assert isinstance(rule["channels"], list)
        assert isinstance(rule["description"], str)
        assert rule["priority"] in ["high", "medium", "low"]


def test_should_notify_with_default() -> None:
    """Test should_notify with default settings."""
    # Discussion mention is enabled by default
    assert should_notify(EventType.DISCUSSION_MENTION) is True

    # Thread added is disabled by default
    assert should_notify(EventType.DISCUSSION_THREAD_ADDED) is False

    # Unknown event type should return False
    assert should_notify("unknown.event.type") is False


def test_should_notify_with_user_preferences() -> None:
    """Test should_notify with user preferences."""
    user_prefs = {
        EventType.DISCUSSION_MENTION: {"enabled": False},
        EventType.DISCUSSION_THREAD_ADDED: {"enabled": True},
    }

    # User disabled mention notifications
    assert should_notify(EventType.DISCUSSION_MENTION, user_prefs) is False

    # User enabled thread notifications (overriding default)
    assert should_notify(EventType.DISCUSSION_THREAD_ADDED, user_prefs) is True

    # Event not in user prefs uses default
    assert should_notify(EventType.DISCUSSION_REPLY_ADDED, user_prefs) is True


def test_get_default_channels() -> None:
    """Test getting default channels for event types."""
    # Mention should have multiple channels
    mention_channels = get_default_channels(EventType.DISCUSSION_MENTION)
    assert "in_app" in mention_channels
    assert "email" in mention_channels

    # Thread added should only have in_app
    thread_channels = get_default_channels(EventType.DISCUSSION_THREAD_ADDED)
    assert "in_app" in thread_channels
    assert "email" not in thread_channels

    # Unknown event type should default to in_app
    unknown_channels = get_default_channels("unknown.event")
    assert unknown_channels == ["in_app"]


def test_get_notification_priority() -> None:
    """Test getting notification priority."""
    # High priority events
    assert get_notification_priority(EventType.DISCUSSION_MENTION) == "high"
    assert get_notification_priority("pgn.export.completed") == "high"

    # Medium priority events
    assert get_notification_priority(EventType.DISCUSSION_REPLY_ADDED) == "medium"

    # Low priority events
    assert get_notification_priority(EventType.DISCUSSION_THREAD_RESOLVED) == "low"

    # Unknown event type should default to low
    assert get_notification_priority("unknown.event") == "low"


def test_get_all_notification_types() -> None:
    """Test getting all notification types."""
    all_types = get_all_notification_types()

    assert isinstance(all_types, dict)
    assert len(all_types) > 0

    # Verify it's a copy (modifying it shouldn't affect original)
    all_types["new.event"] = {"test": "data"}
    assert "new.event" not in NOTIFICATION_RULES


def test_notification_rules_coverage() -> None:
    """Test that key event types have notification rules."""
    required_events = [
        EventType.DISCUSSION_MENTION,
        EventType.DISCUSSION_REPLY_ADDED,
        EventType.DISCUSSION_THREAD_RESOLVED,
        EventType.DISCUSSION_REACTION_ADDED,
    ]

    for event_type in required_events:
        assert event_type in NOTIFICATION_RULES, f"Missing notification rule for {event_type}"


def test_channel_consistency() -> None:
    """Test that all notification rules use valid channel names."""
    valid_channels = ["in_app", "email", "push"]

    for event_type, rule in NOTIFICATION_RULES.items():
        for channel in rule["channels"]:
            assert channel in valid_channels, f"Invalid channel '{channel}' in {event_type}"


def test_priority_consistency() -> None:
    """Test that priorities are consistently used."""
    valid_priorities = ["high", "medium", "low"]

    for event_type, rule in NOTIFICATION_RULES.items():
        assert rule["priority"] in valid_priorities, f"Invalid priority in {event_type}"


def test_description_exists() -> None:
    """Test that all rules have non-empty descriptions."""
    for event_type, rule in NOTIFICATION_RULES.items():
        assert len(rule["description"]) > 0, f"Empty description for {event_type}"


def test_high_priority_events_have_email() -> None:
    """Test that high priority events typically include email channel."""
    high_priority_events = [
        k for k, v in NOTIFICATION_RULES.items() if v["priority"] == "high"
    ]

    # Most high priority events should have email channel
    email_count = sum(
        1
        for event_type in high_priority_events
        if "email" in NOTIFICATION_RULES[event_type]["channels"]
    )

    # At least half of high priority events should have email
    assert email_count >= len(high_priority_events) / 2
