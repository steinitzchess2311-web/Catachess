"""
Presence service for managing user presence in studies.

This service provides high-level operations for managing user presence,
including heartbeat processing, online user tracking, and cursor position updates.
"""

import uuid
from datetime import datetime, UTC, timedelta
from typing import List
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from workspace.collaboration.presence_manager import PresenceManager
from workspace.db.repos.presence_repo import PresenceRepository
from workspace.db.tables.presence_sessions import PresenceSessionTable
from workspace.domain.models.presence import PresenceSession, CursorPosition
from workspace.domain.models.types import PresenceStatus
from workspace.events.bus import EventBus
from workspace.events.types import EventType

logger = logging.getLogger(__name__)


class PresenceServiceError(Exception):
    """Base exception for presence service errors."""
    pass


class SessionNotFoundError(PresenceServiceError):
    """Session not found."""
    pass


class PresenceService:
    """
    Presence service for managing user presence.

    Handles:
    - Creating and managing presence sessions
    - Processing heartbeat updates
    - Tracking online users
    - Cleaning up expired sessions
    """

    def __init__(
        self,
        session: AsyncSession,
        presence_repo: PresenceRepository,
        event_bus: EventBus,
    ) -> None:
        """
        Initialize service.

        Args:
            session: Database session
            presence_repo: Presence repository
            event_bus: Event bus for publishing events
        """
        self.session = session
        self.presence_repo = presence_repo
        self.event_bus = event_bus
        self.presence_manager = PresenceManager(event_bus)

    def _table_to_model(self, table: PresenceSessionTable) -> PresenceSession:
        """Convert table row to domain model."""
        return PresenceSession(
            id=table.id,
            user_id=table.user_id,
            study_id=table.study_id,
            chapter_id=table.chapter_id,
            move_path=table.move_path,
            status=PresenceStatus(table.status),
            last_heartbeat=table.last_heartbeat,
            created_at=table.created_at,
            updated_at=table.updated_at,
        )

    def _model_to_table(self, model: PresenceSession) -> PresenceSessionTable:
        """Convert domain model to table row."""
        return PresenceSessionTable(
            id=model.id,
            user_id=model.user_id,
            study_id=model.study_id,
            chapter_id=model.chapter_id,
            move_path=model.move_path,
            status=model.status.value,
            last_heartbeat=model.last_heartbeat,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def heartbeat(
        self,
        user_id: str,
        study_id: str,
        chapter_id: str | None = None,
        move_path: str | None = None,
    ) -> PresenceSession:
        """
        Process a heartbeat update.

        Creates a new session if one doesn't exist, or updates existing session.

        Args:
            user_id: User ID
            study_id: Study ID
            chapter_id: Optional chapter ID for cursor position
            move_path: Optional move path for cursor position

        Returns:
            Updated presence session
        """
        # Get or create session
        table = await self.presence_repo.get_by_user_study(user_id, study_id)

        if table is None:
            # Create new session
            session_id = str(uuid.uuid4())
            model = PresenceSession(
                id=session_id,
                user_id=user_id,
                study_id=study_id,
                chapter_id=chapter_id,
                move_path=move_path,
                status=PresenceStatus.ACTIVE,
                last_heartbeat=datetime.now(UTC),
            )

            table = self._model_to_table(model)
            table = await self.presence_repo.create(table)

            # Publish user joined event
            await self.event_bus.publish(
                event_type=EventType.PRESENCE_USER_JOINED,
                actor_id=user_id,
                target_id=study_id,
                target_type="study",
                payload={
                    "session_id": session_id,
                    "user_id": user_id,
                    "study_id": study_id,
                    "chapter_id": chapter_id,
                    "move_path": move_path,
                }
            )

            logger.info(f"New presence session created: user={user_id} study={study_id}")
        else:
            # Update existing session
            model = self._table_to_model(table)

        # Process heartbeat through presence manager
        model = await self.presence_manager.process_heartbeat(
            session=model,
            chapter_id=chapter_id,
            move_path=move_path,
        )

        # Update database
        table.chapter_id = model.chapter_id
        table.move_path = model.move_path
        table.status = model.status.value
        table.last_heartbeat = model.last_heartbeat
        table.updated_at = model.updated_at

        await self.presence_repo.update(table)

        return model

    async def get_online_users(self, study_id: str) -> List[PresenceSession]:
        """
        Get list of online users for a study.

        Args:
            study_id: Study ID

        Returns:
            List of active presence sessions
        """
        tables = await self.presence_repo.get_by_study(study_id)
        return [self._table_to_model(t) for t in tables]

    async def update_cursor_position(
        self,
        user_id: str,
        study_id: str,
        chapter_id: str,
        move_path: str | None = None,
    ) -> PresenceSession:
        """
        Update user's cursor position.

        Args:
            user_id: User ID
            study_id: Study ID
            chapter_id: Chapter ID
            move_path: Optional move path

        Returns:
            Updated presence session

        Raises:
            SessionNotFoundError: If session not found
        """
        table = await self.presence_repo.get_by_user_study(user_id, study_id)
        if table is None:
            raise SessionNotFoundError(
                f"No active session found for user={user_id} study={study_id}"
            )

        model = self._table_to_model(table)
        model.chapter_id = chapter_id
        model.move_path = move_path
        model.updated_at = datetime.now(UTC)

        # Update database
        table.chapter_id = chapter_id
        table.move_path = move_path
        table.updated_at = model.updated_at

        await self.presence_repo.update(table)

        # Publish cursor move event
        await self.event_bus.publish(
            event_type=EventType.PRESENCE_CURSOR_MOVED,
            actor_id=user_id,
            target_id=study_id,
            target_type="study",
            payload={
                "session_id": model.id,
                "user_id": user_id,
                "study_id": study_id,
                "chapter_id": chapter_id,
                "move_path": move_path,
            }
        )

        return model

    async def leave_study(self, user_id: str, study_id: str) -> None:
        """
        Remove user from study (delete their session).

        Args:
            user_id: User ID
            study_id: Study ID
        """
        table = await self.presence_repo.get_by_user_study(user_id, study_id)
        if table is not None:
            await self.presence_repo.delete_by_id(table.id)

            # Publish user left event
            await self.event_bus.publish(
                event_type=EventType.PRESENCE_USER_LEFT,
                actor_id=user_id,
                target_id=study_id,
                target_type="study",
                payload={
                    "session_id": table.id,
                    "user_id": user_id,
                    "study_id": study_id,
                }
            )

            logger.info(f"User left study: user={user_id} study={study_id}")

    async def cleanup_expired_sessions(
        self, timeout_minutes: int = 10
    ) -> int:
        """
        Clean up expired sessions.

        Args:
            timeout_minutes: Timeout in minutes (default: 10)

        Returns:
            Number of sessions cleaned up
        """
        threshold = datetime.now(UTC) - timedelta(minutes=timeout_minutes)

        # Get expired sessions for event publishing
        expired_tables = await self.presence_repo.list_expired(threshold)

        # Publish user left events
        for table in expired_tables:
            await self.event_bus.publish(
                event_type=EventType.PRESENCE_USER_LEFT,
                actor_id=table.user_id,
                target_id=table.study_id,
                target_type="study",
                payload={
                    "session_id": table.id,
                    "user_id": table.user_id,
                    "study_id": table.study_id,
                    "reason": "timeout",
                }
            )

        # Delete expired sessions
        count = await self.presence_repo.delete_expired(threshold)

        if count > 0:
            logger.info(f"Cleaned up {count} expired presence sessions")

        return count

    async def update_all_statuses(self) -> List[PresenceSession]:
        """
        Update status for all sessions based on last heartbeat.

        Should be called periodically to transition sessions between
        active/idle/away states.

        Returns:
            List of updated sessions
        """
        # Get all sessions from all studies (this might need optimization for scale)
        # For now, we'll implement a simple version
        # In production, you might want to batch this or use a different approach

        # This is a placeholder - in a real implementation,
        # you'd need a way to get all sessions efficiently
        # For now, this method is primarily for the cleanup job

        logger.debug("Status update called - implement batching for production")
        return []
