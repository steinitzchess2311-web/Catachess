"""
Presence manager for handling heartbeats and status updates.

This module implements the core logic for managing user presence sessions,
including heartbeat processing, status transitions, and session cleanup.
"""

from datetime import datetime, UTC
from typing import List
import logging

from ..domain.models.presence import PresenceSession, PresenceStatus
from ..domain.models.event import CreateEventCommand
from ..events.bus import EventBus
from ..events.types import EventType

logger = logging.getLogger(__name__)


class PresenceManager:
    """
    Presence manager for handling real-time user presence.

    Responsibilities:
    - Process heartbeat updates
    - Manage status transitions (active → idle → away)
    - Clean up expired sessions
    - Publish presence events
    """

    def __init__(self, event_bus: EventBus):
        """
        Initialize the presence manager.

        Args:
            event_bus: Event bus for publishing presence events
        """
        self.event_bus = event_bus

    async def process_heartbeat(
        self,
        session: PresenceSession,
        chapter_id: str | None = None,
        move_path: str | None = None
    ) -> PresenceSession:
        """
        Process a heartbeat update for a session.

        Args:
            session: The presence session to update
            chapter_id: Optional chapter ID for cursor position
            move_path: Optional move path for cursor position

        Returns:
            The updated session
        """
        old_status = session.status
        old_chapter = session.chapter_id
        old_move_path = session.move_path

        # Update heartbeat and cursor position
        session.update_heartbeat(chapter_id=chapter_id, move_path=move_path)

        # Publish events
        if old_status != PresenceStatus.ACTIVE:
            await self._publish_status_change(
                session=session,
                old_status=old_status,
                new_status=PresenceStatus.ACTIVE
            )

        # Publish cursor move event if position changed
        if (chapter_id and chapter_id != old_chapter) or (move_path and move_path != old_move_path):
            await self._publish_cursor_move(session)

        logger.debug(
            f"Heartbeat processed for user {session.user_id} in study {session.study_id}"
        )

        return session

    async def update_session_statuses(self, sessions: List[PresenceSession]) -> List[PresenceSession]:
        """
        Update status for multiple sessions based on elapsed time.

        This should be called periodically to transition sessions
        from active → idle → away based on heartbeat timeout.

        Args:
            sessions: List of sessions to update

        Returns:
            List of sessions with updated statuses
        """
        updated_sessions = []

        for session in sessions:
            elapsed = session.time_since_last_heartbeat()
            old_status = session.status
            new_status = session.update_status(elapsed)

            if old_status != new_status:
                await self._publish_status_change(
                    session=session,
                    old_status=old_status,
                    new_status=new_status
                )
                logger.info(
                    f"Status transition: user={session.user_id} study={session.study_id} "
                    f"{old_status} → {new_status}"
                )

            updated_sessions.append(session)

        return updated_sessions

    async def cleanup_expired_sessions(
        self,
        sessions: List[PresenceSession],
        timeout_seconds: int = 600
    ) -> List[str]:
        """
        Identify and cleanup expired sessions.

        Args:
            sessions: List of sessions to check
            timeout_seconds: Timeout threshold in seconds (default: 10 minutes)

        Returns:
            List of expired session IDs that should be removed
        """
        expired_ids = []

        for session in sessions:
            if session.is_expired(timeout_seconds):
                expired_ids.append(session.id)
                await self._publish_user_left(session)
                logger.info(
                    f"Session expired: user={session.user_id} study={session.study_id} "
                    f"last_heartbeat={session.last_heartbeat}"
                )

        return expired_ids

    async def _publish_status_change(
        self,
        session: PresenceSession,
        old_status: PresenceStatus,
        new_status: PresenceStatus
    ) -> None:
        """Publish presence status change event."""
        event_type_map = {
            PresenceStatus.ACTIVE: EventType.PRESENCE_USER_ACTIVE,
            PresenceStatus.IDLE: EventType.PRESENCE_USER_IDLE,
            PresenceStatus.AWAY: EventType.PRESENCE_USER_AWAY,
        }

        event_type = event_type_map.get(new_status)
        if not event_type:
            logger.warning(f"Unknown presence status: {new_status}")
            return

        command = CreateEventCommand(
            type=event_type,
            actor_id=session.user_id,
            target_id=session.study_id,
            target_type="study",
            version=1,
            payload={
                "session_id": session.id,
                "user_id": session.user_id,
                "study_id": session.study_id,
                "old_status": old_status.value,
                "new_status": new_status.value,
                "chapter_id": session.chapter_id,
                "move_path": session.move_path,
            },
        )
        await self.event_bus.publish(command)

    async def _publish_cursor_move(self, session: PresenceSession) -> None:
        """Publish cursor position update event."""
        command = CreateEventCommand(
            type=EventType.PRESENCE_CURSOR_MOVED,
            actor_id=session.user_id,
            target_id=session.study_id,
            target_type="study",
            version=1,
            payload={
                "session_id": session.id,
                "user_id": session.user_id,
                "study_id": session.study_id,
                "chapter_id": session.chapter_id,
                "move_path": session.move_path,
            },
        )
        await self.event_bus.publish(command)

    async def _publish_user_left(self, session: PresenceSession) -> None:
        """Publish user left event."""
        command = CreateEventCommand(
            type=EventType.PRESENCE_USER_LEFT,
            actor_id=session.user_id,
            target_id=session.study_id,
            target_type="study",
            version=1,
            payload={
                "session_id": session.id,
                "user_id": session.user_id,
                "study_id": session.study_id,
            },
        )
        await self.event_bus.publish(command)
