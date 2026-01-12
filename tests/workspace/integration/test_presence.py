"""
Integration tests for presence system.

Tests the complete presence flow including service, repository,
event publishing, and cleanup.
"""

import pytest
from datetime import datetime, UTC, timedelta

from workspace.db.repos.presence_repo import PresenceRepository
from workspace.domain.services.presence_service import PresenceService
from workspace.events.bus import EventBus
from workspace.domain.models.types import PresenceStatus


@pytest.fixture
async def presence_repo(session):
    """Create presence repository."""
    return PresenceRepository(session)


@pytest.fixture
async def presence_service(session, presence_repo, event_bus):
    """Create presence service."""
    return PresenceService(
        session=session,
        presence_repo=presence_repo,
        event_bus=event_bus
    )


@pytest.mark.asyncio
class TestPresenceIntegration:
    """Integration tests for presence system."""

    async def test_heartbeat_creates_new_session(
        self, presence_service: PresenceService, session
    ):
        """Test that heartbeat creates a new session if none exists."""
        # Send heartbeat
        presence = await presence_service.heartbeat(
            user_id="user1",
            study_id="study1",
            chapter_id="chapter1",
            move_path="main.5"
        )

        assert presence.user_id == "user1"
        assert presence.study_id == "study1"
        assert presence.chapter_id == "chapter1"
        assert presence.move_path == "main.5"
        assert presence.status == PresenceStatus.ACTIVE

        await session.commit()

    async def test_heartbeat_updates_existing_session(
        self, presence_service: PresenceService, session
    ):
        """Test that heartbeat updates existing session."""
        # Create initial session
        session1 = await presence_service.heartbeat(
            user_id="user1",
            study_id="study1",
            chapter_id="chapter1",
            move_path="main.5"
        )

        initial_id = session1.id
        await session.commit()

        # Send another heartbeat with updated position
        session2 = await presence_service.heartbeat(
            user_id="user1",
            study_id="study1",
            chapter_id="chapter2",
            move_path="main.12"
        )

        # Should update same session, not create new one
        assert session2.id == initial_id
        assert session2.chapter_id == "chapter2"
        assert session2.move_path == "main.12"
        assert session2.last_heartbeat > session1.last_heartbeat

    async def test_get_online_users_returns_active_sessions(
        self, presence_service: PresenceService, session
    ):
        """Test getting list of online users."""
        # Create multiple sessions
        await presence_service.heartbeat("user1", "study1", "chapter1")
        await presence_service.heartbeat("user2", "study1", "chapter2")
        await presence_service.heartbeat("user3", "study2", "chapter1")
        await session.commit()

        # Get online users for study1
        users = await presence_service.get_online_users("study1")

        assert len(users) == 2
        user_ids = [u.user_id for u in users]
        assert "user1" in user_ids
        assert "user2" in user_ids
        assert "user3" not in user_ids

    async def test_leave_study_removes_session(
        self, presence_service: PresenceService, session
    ):
        """Test that leaving a study removes the session."""
        # Create session
        await presence_service.heartbeat("user1", "study1", "chapter1")
        await session.commit()

        # Verify session exists
        users = await presence_service.get_online_users("study1")
        assert len(users) == 1

        # Leave study
        await presence_service.leave_study("user1", "study1")
        await session.commit()

        # Verify session removed
        users = await presence_service.get_online_users("study1")
        assert len(users) == 0

    async def test_cleanup_expired_sessions(
        self, presence_service: PresenceService, presence_repo, session
    ):
        """Test cleanup of expired sessions."""
        # Create recent session
        await presence_service.heartbeat("user1", "study1", "chapter1")
        await session.commit()

        # Create expired session by directly manipulating DB
        from workspace.db.tables.presence_sessions import PresenceSessionTable
        expired_session = PresenceSessionTable(
            id="expired1",
            user_id="user2",
            study_id="study1",
            chapter_id="chapter1",
            move_path=None,
            status="active",
            last_heartbeat=datetime.now(UTC) - timedelta(minutes=15)
        )
        session.add(expired_session)
        await session.commit()

        # Verify both sessions exist
        all_users = await presence_service.get_online_users("study1")
        assert len(all_users) == 2

        # Run cleanup (10 minute timeout)
        count = await presence_service.cleanup_expired_sessions(timeout_minutes=10)
        await session.commit()

        # Should have cleaned up 1 expired session
        assert count == 1

        # Verify only active session remains
        remaining_users = await presence_service.get_online_users("study1")
        assert len(remaining_users) == 1
        assert remaining_users[0].user_id == "user1"

    async def test_update_cursor_position(
        self, presence_service: PresenceService, session
    ):
        """Test updating cursor position."""
        # Create session
        await presence_service.heartbeat("user1", "study1", "chapter1", "main.5")
        await session.commit()

        # Update cursor position
        updated = await presence_service.update_cursor_position(
            user_id="user1",
            study_id="study1",
            chapter_id="chapter2",
            move_path="main.12.var2.3"
        )

        assert updated.chapter_id == "chapter2"
        assert updated.move_path == "main.12.var2.3"

    async def test_multiple_studies_isolation(
        self, presence_service: PresenceService, session
    ):
        """Test that presence sessions are isolated per study."""
        # User in multiple studies
        await presence_service.heartbeat("user1", "study1", "chapter1")
        await presence_service.heartbeat("user1", "study2", "chapter1")
        await session.commit()

        # Check each study separately
        study1_users = await presence_service.get_online_users("study1")
        study2_users = await presence_service.get_online_users("study2")

        assert len(study1_users) == 1
        assert len(study2_users) == 1
        assert study1_users[0].user_id == "user1"
        assert study2_users[0].user_id == "user1"

    async def test_concurrent_heartbeats_same_user(
        self, presence_service: PresenceService, session
    ):
        """Test multiple heartbeats from same user in quick succession."""
        # Send multiple heartbeats
        session1 = await presence_service.heartbeat("user1", "study1", "chapter1", "main.1")
        await session.commit()

        session2 = await presence_service.heartbeat("user1", "study1", "chapter1", "main.2")
        await session.commit()

        session3 = await presence_service.heartbeat("user1", "study1", "chapter1", "main.3")
        await session.commit()

        # Should all be same session with updated position
        assert session1.id == session2.id == session3.id
        assert session3.move_path == "main.3"

        # Should still only be one session
        users = await presence_service.get_online_users("study1")
        assert len(users) == 1

    async def test_cursor_position_none_handling(
        self, presence_service: PresenceService, session
    ):
        """Test handling of None cursor position."""
        # Create session without cursor
        presence = await presence_service.heartbeat("user1", "study1")

        assert presence.chapter_id is None
        assert presence.move_path is None
        assert presence.cursor_position is None

    async def test_events_published_on_heartbeat(
        self, presence_service: PresenceService, event_bus: EventBus, session
    ):
        """Test that events are published on heartbeat."""
        # First heartbeat should publish user_joined event
        await presence_service.heartbeat("user1", "study1", "chapter1")
        await session.commit()

        # Check events were published
        events = await event_bus.get_events_for_target("study1", "study")

        # Should have at least the joined event
        assert len(events) > 0
        event_types = [e.event_type for e in events]
        assert "presence.user_joined" in event_types
