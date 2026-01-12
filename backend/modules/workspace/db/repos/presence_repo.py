"""
Presence repository for database operations.

Handles CRUD operations for presence sessions.
"""

from datetime import datetime
from typing import List

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from workspace.db.tables.presence_sessions import PresenceSessionTable


class PresenceRepository:
    """Repository for presence session database operations."""

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize repository.

        Args:
            session: Database session
        """
        self.session = session

    async def create(self, session_data: PresenceSessionTable) -> PresenceSessionTable:
        """
        Create a new presence session.

        Args:
            session_data: Session data to create

        Returns:
            Created session
        """
        self.session.add(session_data)
        await self.session.flush()
        await self.session.refresh(session_data)
        return session_data

    async def get_by_id(self, session_id: str) -> PresenceSessionTable | None:
        """
        Get session by ID.

        Args:
            session_id: Session ID

        Returns:
            Session or None if not found
        """
        result = await self.session.execute(
            select(PresenceSessionTable).where(PresenceSessionTable.id == session_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user_study(
        self, user_id: str, study_id: str
    ) -> PresenceSessionTable | None:
        """
        Get session by user and study.

        Args:
            user_id: User ID
            study_id: Study ID

        Returns:
            Session or None if not found
        """
        result = await self.session.execute(
            select(PresenceSessionTable).where(
                PresenceSessionTable.user_id == user_id,
                PresenceSessionTable.study_id == study_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_study(self, study_id: str) -> List[PresenceSessionTable]:
        """
        Get all sessions for a study.

        Args:
            study_id: Study ID

        Returns:
            List of sessions
        """
        result = await self.session.execute(
            select(PresenceSessionTable).where(
                PresenceSessionTable.study_id == study_id
            )
        )
        return list(result.scalars().all())

    async def get_by_user(self, user_id: str) -> List[PresenceSessionTable]:
        """
        Get all sessions for a user.

        Args:
            user_id: User ID

        Returns:
            List of sessions
        """
        result = await self.session.execute(
            select(PresenceSessionTable).where(
                PresenceSessionTable.user_id == user_id
            )
        )
        return list(result.scalars().all())

    async def update(self, session_data: PresenceSessionTable) -> PresenceSessionTable:
        """
        Update a session.

        Args:
            session_data: Session data to update

        Returns:
            Updated session
        """
        await self.session.flush()
        await self.session.refresh(session_data)
        return session_data

    async def delete_by_id(self, session_id: str) -> None:
        """
        Delete a session by ID.

        Args:
            session_id: Session ID
        """
        await self.session.execute(
            delete(PresenceSessionTable).where(PresenceSessionTable.id == session_id)
        )

    async def delete_expired(self, before: datetime) -> int:
        """
        Delete sessions with last_heartbeat before the given time.

        Args:
            before: Timestamp threshold

        Returns:
            Number of deleted sessions
        """
        result = await self.session.execute(
            delete(PresenceSessionTable).where(
                PresenceSessionTable.last_heartbeat < before
            )
        )
        return result.rowcount

    async def list_expired(self, before: datetime) -> List[PresenceSessionTable]:
        """
        List sessions with last_heartbeat before the given time.

        Args:
            before: Timestamp threshold

        Returns:
            List of expired sessions
        """
        result = await self.session.execute(
            select(PresenceSessionTable).where(
                PresenceSessionTable.last_heartbeat < before
            )
        )
        return list(result.scalars().all())
