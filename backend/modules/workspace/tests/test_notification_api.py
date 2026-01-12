"""Tests for notification API endpoints."""
import uuid
from datetime import UTC, datetime

import httpx
import pytest
from httpx import ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from workspace.api.app import app
from workspace.db.repos.notification_repo import NotificationRepository
from workspace.db.repos.notification_preference_repo import NotificationPreferenceRepository
from workspace.db.tables.notification_preferences import NotificationPreference
from workspace.db.tables.notifications import Notification


@pytest.fixture
async def notification_repo(session: AsyncSession) -> NotificationRepository:
    """Get notification repository."""
    return NotificationRepository(session)


@pytest.fixture
async def preference_repo(session: AsyncSession) -> NotificationPreferenceRepository:
    """Get preference repository."""
    return NotificationPreferenceRepository(session)


@pytest.fixture
async def test_user_id() -> str:
    """Get test user ID."""
    return str(uuid.uuid4())


@pytest.fixture
async def test_notification(
    notification_repo: NotificationRepository, test_user_id: str, session: AsyncSession
) -> Notification:
    """Create a test notification."""
    notification = Notification(
        id=str(uuid.uuid4()),
        user_id=test_user_id,
        event_type="discussion.mention",
        payload={"test": "data"},
    )
    notification = await notification_repo.create(notification)
    await session.commit()
    return notification


@pytest.fixture
async def test_preferences(
    preference_repo: NotificationPreferenceRepository, test_user_id: str, session: AsyncSession
) -> NotificationPreference:
    """Create test notification preferences."""
    prefs = NotificationPreference(
        id=str(uuid.uuid4()),
        user_id=test_user_id,
        preferences={
            "discussion.mention": {"enabled": True, "channels": ["in_app", "email"]}
        },
        digest_frequency="instant",
        quiet_hours={},
        muted_objects=[],
        enabled=True,
    )
    prefs = await preference_repo.create(prefs)
    await session.commit()
    return prefs


@pytest.mark.asyncio
async def test_list_notifications(test_user_id: str, test_notification: Notification) -> None:
    """Test listing user notifications."""
    async with httpx.AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/notifications",
            headers={"X-User-ID": test_user_id},
        )

    assert response.status_code == 200
    data = response.json()
    assert "notifications" in data
    assert "total" in data
    assert "unread_count" in data
    assert data["total"] >= 1
    assert len(data["notifications"]) >= 1
    assert data["notifications"][0]["id"] == test_notification.id


@pytest.mark.asyncio
async def test_list_notifications_pagination(
    test_user_id: str, notification_repo: NotificationRepository, session: AsyncSession
) -> None:
    """Test notification pagination."""
    # Create multiple notifications
    for i in range(5):
        notification = Notification(
            id=str(uuid.uuid4()),
            user_id=test_user_id,
            event_type="test.event",
            payload={"index": i},
        )
        await notification_repo.create(notification)
    await session.commit()

    async with httpx.AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/notifications?page=1&page_size=2",
            headers={"X-User-ID": test_user_id},
        )

    assert response.status_code == 200
    data = response.json()
    assert len(data["notifications"]) == 2
    assert data["page"] == 1
    assert data["page_size"] == 2


@pytest.mark.asyncio
async def test_list_unread_only(
    test_user_id: str, notification_repo: NotificationRepository, session: AsyncSession
) -> None:
    """Test filtering unread notifications."""
    # Create unread notification
    unread = Notification(
        id=str(uuid.uuid4()),
        user_id=test_user_id,
        event_type="test.unread",
        payload={},
    )
    await notification_repo.create(unread)

    # Create read notification
    read = Notification(
        id=str(uuid.uuid4()),
        user_id=test_user_id,
        event_type="test.read",
        payload={},
        read_at=datetime.now(UTC),
    )
    await notification_repo.create(read)
    await session.commit()

    async with httpx.AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/notifications?unread_only=true",
            headers={"X-User-ID": test_user_id},
        )

    assert response.status_code == 200
    data = response.json()
    # Should only get unread notifications
    notification_ids = [n["id"] for n in data["notifications"]]
    assert unread.id in notification_ids
    assert read.id not in notification_ids


@pytest.mark.asyncio
async def test_mark_notifications_read(test_user_id: str, test_notification: Notification) -> None:
    """Test marking notifications as read."""
    async with httpx.AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/notifications/read",
            json={"notification_ids": [test_notification.id]},
            headers={"X-User-ID": test_user_id},
        )

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_mark_read_forbidden(test_notification: Notification) -> None:
    """Test marking other user's notifications as read fails."""
    other_user_id = str(uuid.uuid4())

    async with httpx.AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/notifications/read",
            json={"notification_ids": [test_notification.id]},
            headers={"X-User-ID": other_user_id},
        )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_bulk_mark_all_read(
    test_user_id: str, notification_repo: NotificationRepository, session: AsyncSession
) -> None:
    """Test bulk marking all notifications as read."""
    # Create multiple unread notifications
    for i in range(3):
        notification = Notification(
            id=str(uuid.uuid4()),
            user_id=test_user_id,
            event_type="test.event",
            payload={"index": i},
        )
        await notification_repo.create(notification)
    await session.commit()

    async with httpx.AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/notifications/bulk-read",
            json={"mark_all": True},
            headers={"X-User-ID": test_user_id},
        )

    assert response.status_code == 204

    # Verify all are read
    unread = await notification_repo.get_unread(test_user_id)
    assert len(unread) == 0


@pytest.mark.asyncio
async def test_delete_notification(test_user_id: str, test_notification: Notification) -> None:
    """Test deleting a notification."""
    async with httpx.AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.delete(
            f"/notifications/{test_notification.id}",
            headers={"X-User-ID": test_user_id},
        )

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_notification_forbidden(test_notification: Notification) -> None:
    """Test deleting other user's notification fails."""
    other_user_id = str(uuid.uuid4())

    async with httpx.AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.delete(
            f"/notifications/{test_notification.id}",
            headers={"X-User-ID": other_user_id},
        )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_preferences_creates_default(test_user_id: str) -> None:
    """Test getting preferences creates default if not exists."""
    async with httpx.AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/notifications/preferences",
            headers={"X-User-ID": test_user_id},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == test_user_id
    assert data["enabled"] is True
    assert data["digest_frequency"] == "instant"


@pytest.mark.asyncio
async def test_update_preferences(test_user_id: str, test_preferences: NotificationPreference) -> None:
    """Test updating notification preferences."""
    new_prefs = {
        "preferences": {
            "discussion.mention": {"enabled": False, "channels": ["in_app"]}
        },
        "digest_frequency": "daily",
        "quiet_hours": {"enabled": True, "start_hour": 22, "end_hour": 8},
        "muted_objects": ["study-123"],
        "enabled": True,
    }

    async with httpx.AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.put(
            "/notifications/preferences",
            json=new_prefs,
            headers={"X-User-ID": test_user_id},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["digest_frequency"] == "daily"
    assert data["quiet_hours"]["enabled"] is True
    assert "study-123" in data["muted_objects"]


@pytest.mark.asyncio
async def test_list_notification_types() -> None:
    """Test listing all notification types."""
    async with httpx.AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/notifications/types")

    assert response.status_code == 200
    data = response.json()
    assert "types" in data
    assert len(data["types"]) > 0

    # Check structure of notification types
    first_type = data["types"][0]
    assert "event_type" in first_type
    assert "enabled_by_default" in first_type
    assert "channels" in first_type
    assert "description" in first_type
    assert "priority" in first_type
