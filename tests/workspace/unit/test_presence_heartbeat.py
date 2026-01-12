"""
Unit tests for presence heartbeat functionality.

Tests the core heartbeat processing logic, status transitions,
and session lifecycle management.
"""

import pytest
from datetime import datetime, UTC, timedelta

from workspace.domain.models.presence import PresenceSession, PresenceStatus
from workspace.collaboration.presence_manager import PresenceManager
from workspace.events.bus import EventBus


@pytest.mark.asyncio
class TestPresenceHeartbeat:
    """Test presence heartbeat functionality."""

    async def test_new_session_starts_active(self):
        """Test that new sessions start with ACTIVE status."""
        session = PresenceSession(
            id="session1",
            user_id="user1",
            study_id="study1",
            chapter_id="chapter1",
            move_path="main.12",
            status=PresenceStatus.ACTIVE,
            last_heartbeat=datetime.now(UTC),
        )

        assert session.status == PresenceStatus.ACTIVE
        assert session.cursor_position is not None
        assert session.cursor_position.chapter_id == "chapter1"
        assert session.cursor_position.move_path == "main.12"

    async def test_heartbeat_updates_timestamp(self):
        """Test that heartbeat updates the last_heartbeat timestamp."""
        session = PresenceSession(
            id="session1",
            user_id="user1",
            study_id="study1",
            chapter_id=None,
            move_path=None,
            status=PresenceStatus.ACTIVE,
            last_heartbeat=datetime.now(UTC) - timedelta(seconds=60),
        )

        old_heartbeat = session.last_heartbeat
        session.update_heartbeat()

        assert session.last_heartbeat > old_heartbeat
        assert session.status == PresenceStatus.ACTIVE

    async def test_heartbeat_updates_cursor_position(self):
        """Test that heartbeat can update cursor position."""
        session = PresenceSession(
            id="session1",
            user_id="user1",
            study_id="study1",
            chapter_id="chapter1",
            move_path="main.5",
            status=PresenceStatus.ACTIVE,
            last_heartbeat=datetime.now(UTC),
        )

        session.update_heartbeat(chapter_id="chapter2", move_path="main.12.var2.3")

        assert session.chapter_id == "chapter2"
        assert session.move_path == "main.12.var2.3"
        assert session.cursor_position.chapter_id == "chapter2"
        assert session.cursor_position.move_path == "main.12.var2.3"

    async def test_status_transition_to_idle(self):
        """Test status transition from ACTIVE to IDLE after 30s."""
        session = PresenceSession(
            id="session1",
            user_id="user1",
            study_id="study1",
            chapter_id=None,
            move_path=None,
            status=PresenceStatus.ACTIVE,
            last_heartbeat=datetime.now(UTC) - timedelta(seconds=45),
        )

        elapsed = session.time_since_last_heartbeat()
        new_status = session.update_status(elapsed)

        assert new_status == PresenceStatus.IDLE
        assert session.status == PresenceStatus.IDLE

    async def test_status_transition_to_away(self):
        """Test status transition from IDLE to AWAY after 5min."""
        session = PresenceSession(
            id="session1",
            user_id="user1",
            study_id="study1",
            chapter_id=None,
            move_path=None,
            status=PresenceStatus.IDLE,
            last_heartbeat=datetime.now(UTC) - timedelta(minutes=6),
        )

        elapsed = session.time_since_last_heartbeat()
        new_status = session.update_status(elapsed)

        assert new_status == PresenceStatus.AWAY
        assert session.status == PresenceStatus.AWAY

    async def test_status_remains_active_within_threshold(self):
        """Test that status remains ACTIVE within 30s threshold."""
        session = PresenceSession(
            id="session1",
            user_id="user1",
            study_id="study1",
            chapter_id=None,
            move_path=None,
            status=PresenceStatus.ACTIVE,
            last_heartbeat=datetime.now(UTC) - timedelta(seconds=15),
        )

        elapsed = session.time_since_last_heartbeat()
        new_status = session.update_status(elapsed)

        assert new_status == PresenceStatus.ACTIVE
        assert session.status == PresenceStatus.ACTIVE

    async def test_session_expiry_detection(self):
        """Test session expiry detection."""
        # Expired session (> 10min)
        expired_session = PresenceSession(
            id="session1",
            user_id="user1",
            study_id="study1",
            chapter_id=None,
            move_path=None,
            status=PresenceStatus.AWAY,
            last_heartbeat=datetime.now(UTC) - timedelta(minutes=15),
        )

        assert expired_session.is_expired(timeout_seconds=600)  # 10 min

        # Active session
        active_session = PresenceSession(
            id="session2",
            user_id="user2",
            study_id="study1",
            chapter_id=None,
            move_path=None,
            status=PresenceStatus.ACTIVE,
            last_heartbeat=datetime.now(UTC) - timedelta(seconds=30),
        )

        assert not active_session.is_expired(timeout_seconds=600)

    async def test_heartbeat_reactivates_idle_session(self):
        """Test that heartbeat reactivates an IDLE session."""
        session = PresenceSession(
            id="session1",
            user_id="user1",
            study_id="study1",
            chapter_id=None,
            move_path=None,
            status=PresenceStatus.IDLE,
            last_heartbeat=datetime.now(UTC) - timedelta(seconds=60),
        )

        assert session.status == PresenceStatus.IDLE

        session.update_heartbeat()

        assert session.status == PresenceStatus.ACTIVE

    async def test_presence_manager_processes_heartbeat(self):
        """Test PresenceManager processes heartbeat correctly."""
        event_bus = EventBus(session=None)  # Mock event bus
        manager = PresenceManager(event_bus)

        session = PresenceSession(
            id="session1",
            user_id="user1",
            study_id="study1",
            chapter_id="chapter1",
            move_path="main.5",
            status=PresenceStatus.ACTIVE,
            last_heartbeat=datetime.now(UTC) - timedelta(seconds=60),
        )

        # Process heartbeat with new cursor position
        updated_session = await manager.process_heartbeat(
            session=session,
            chapter_id="chapter2",
            move_path="main.12",
        )

        assert updated_session.chapter_id == "chapter2"
        assert updated_session.move_path == "main.12"
        assert updated_session.status == PresenceStatus.ACTIVE

    async def test_time_since_last_heartbeat(self):
        """Test calculating time since last heartbeat."""
        session = PresenceSession(
            id="session1",
            user_id="user1",
            study_id="study1",
            chapter_id=None,
            move_path=None,
            status=PresenceStatus.ACTIVE,
            last_heartbeat=datetime.now(UTC) - timedelta(seconds=42),
        )

        elapsed = session.time_since_last_heartbeat()

        # Should be approximately 42 seconds (with small tolerance for test execution time)
        assert 41 <= elapsed <= 44
