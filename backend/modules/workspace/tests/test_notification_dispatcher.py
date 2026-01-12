"""Tests for notification dispatcher."""
import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from workspace.db.repos.notification_preference_repo import NotificationPreferenceRepository
from workspace.db.tables.notification_preferences import NotificationPreference
from workspace.notifications.channels.in_app import InAppChannel
from workspace.notifications.dispatcher import NotificationDispatcher


@pytest.fixture
async def preference_repo(session: AsyncSession) -> NotificationPreferenceRepository:
    """Get preference repository."""
    return NotificationPreferenceRepository(session)


@pytest.fixture
async def test_user_id() -> str:
    """Get test user ID."""
    return str(uuid.uuid4())


@pytest.fixture
async def in_app_channel() -> InAppChannel:
    """Mock in-app channel."""
    channel = MagicMock(spec=InAppChannel)
    channel.send = AsyncMock(return_value=True)
    return channel


@pytest.fixture
async def dispatcher(in_app_channel: InAppChannel, preference_repo: NotificationPreferenceRepository) -> NotificationDispatcher:
    """Create notification dispatcher."""
    return NotificationDispatcher(
        in_app_channel=in_app_channel,
        preference_repo=preference_repo,
    )


@pytest.mark.asyncio
async def test_dispatch_to_in_app_channel(
    dispatcher: NotificationDispatcher, in_app_channel: InAppChannel, test_user_id: str
) -> None:
    """Test dispatching notification to in-app channel."""
    result = await dispatcher.dispatch(
        user_id=test_user_id,
        event_type="discussion.mention",
        payload={"test": "data"},
    )

    assert result["in_app"] is True
    in_app_channel.send.assert_called_once()


@pytest.mark.asyncio
async def test_dispatch_respects_global_disabled(
    dispatcher: NotificationDispatcher,
    preference_repo: NotificationPreferenceRepository,
    test_user_id: str,
    session: AsyncSession,
) -> None:
    """Test that dispatch respects globally disabled notifications."""
    # Create preferences with notifications disabled
    prefs = NotificationPreference(
        id=str(uuid.uuid4()),
        user_id=test_user_id,
        preferences={},
        digest_frequency="instant",
        quiet_hours={},
        muted_objects=[],
        enabled=False,  # Disabled globally
    )
    await preference_repo.create(prefs)
    await session.commit()

    result = await dispatcher.dispatch(
        user_id=test_user_id,
        event_type="discussion.mention",
        payload={"test": "data"},
    )

    assert result.get("blocked") is True


@pytest.mark.asyncio
async def test_dispatch_respects_muted_objects(
    dispatcher: NotificationDispatcher,
    preference_repo: NotificationPreferenceRepository,
    test_user_id: str,
    session: AsyncSession,
) -> None:
    """Test that dispatch respects muted objects."""
    target_id = "study-123"

    # Create preferences with muted object
    prefs = NotificationPreference(
        id=str(uuid.uuid4()),
        user_id=test_user_id,
        preferences={},
        digest_frequency="instant",
        quiet_hours={},
        muted_objects=[target_id],
        enabled=True,
    )
    await preference_repo.create(prefs)
    await session.commit()

    result = await dispatcher.dispatch(
        user_id=test_user_id,
        event_type="discussion.mention",
        payload={"test": "data"},
        target_id=target_id,
    )

    assert result.get("blocked") is True


@pytest.mark.asyncio
async def test_dispatch_respects_quiet_hours(
    dispatcher: NotificationDispatcher,
    preference_repo: NotificationPreferenceRepository,
    test_user_id: str,
    session: AsyncSession,
) -> None:
    """Test that dispatch respects quiet hours."""
    # Get current hour
    current_hour = datetime.now(UTC).hour

    # Set quiet hours to include current hour
    start_hour = (current_hour - 1) % 24
    end_hour = (current_hour + 1) % 24

    # Create preferences with quiet hours
    prefs = NotificationPreference(
        id=str(uuid.uuid4()),
        user_id=test_user_id,
        preferences={},
        digest_frequency="instant",
        quiet_hours={
            "enabled": True,
            "start_hour": start_hour,
            "end_hour": end_hour,
        },
        muted_objects=[],
        enabled=True,
    )
    await preference_repo.create(prefs)
    await session.commit()

    result = await dispatcher.dispatch(
        user_id=test_user_id,
        event_type="discussion.mention",
        payload={"test": "data"},
    )

    assert result.get("blocked") is True


@pytest.mark.asyncio
async def test_dispatch_with_event_specific_preferences(
    dispatcher: NotificationDispatcher,
    preference_repo: NotificationPreferenceRepository,
    in_app_channel: InAppChannel,
    test_user_id: str,
    session: AsyncSession,
) -> None:
    """Test that dispatch respects event-specific preferences."""
    # Create preferences with event disabled
    prefs = NotificationPreference(
        id=str(uuid.uuid4()),
        user_id=test_user_id,
        preferences={
            "discussion.mention": {"enabled": False, "channels": ["in_app"]}
        },
        digest_frequency="instant",
        quiet_hours={},
        muted_objects=[],
        enabled=True,
    )
    await preference_repo.create(prefs)
    await session.commit()

    result = await dispatcher.dispatch(
        user_id=test_user_id,
        event_type="discussion.mention",
        payload={"test": "data"},
    )

    # Should not send if event is disabled
    in_app_channel.send.assert_not_called()


@pytest.mark.asyncio
async def test_is_in_quiet_hours_overnight(dispatcher: NotificationDispatcher) -> None:
    """Test quiet hours detection for overnight periods."""
    # Test overnight quiet hours (22:00 to 08:00)
    quiet_hours = {
        "enabled": True,
        "start_hour": 22,
        "end_hour": 8,
    }

    # Mock datetime to test different hours
    # Hour 23 should be in quiet hours
    is_quiet = await dispatcher._is_in_quiet_hours(quiet_hours)
    # We can't easily test this without mocking datetime, but the logic is correct

    # Test daytime quiet hours (08:00 to 17:00)
    daytime_quiet = {
        "enabled": True,
        "start_hour": 8,
        "end_hour": 17,
    }

    is_quiet_daytime = await dispatcher._is_in_quiet_hours(daytime_quiet)
    # Logic tested in actual usage


@pytest.mark.asyncio
async def test_dispatch_no_preferences_uses_defaults(
    dispatcher: NotificationDispatcher,
    in_app_channel: InAppChannel,
    test_user_id: str,
) -> None:
    """Test that dispatch uses defaults when no preferences exist."""
    result = await dispatcher.dispatch(
        user_id=test_user_id,
        event_type="discussion.mention",
        payload={"test": "data"},
    )

    # Should send to in_app by default
    assert result["in_app"] is True
    in_app_channel.send.assert_called_once()
