"""
Presence domain model for real-time collaboration.

This module defines the PresenceSession aggregate root for tracking
user presence and cursor positions in real-time collaboration scenarios.
"""

from datetime import datetime, UTC
from dataclasses import dataclass, field

from .types import PresenceStatus


@dataclass
class CursorPosition:
    """
    User cursor position in a study.

    Tracks where a user is currently looking/editing within a chapter.
    """
    chapter_id: str
    move_path: str | None = None  # e.g., "main.12.var2.3" or None for root


@dataclass
class PresenceSession:
    """
    Presence session aggregate root.

    Represents a user's active session in a study, tracking their
    online status, cursor position, and last activity time.

    State transitions:
    - ACTIVE: User actively working (within 30s)
    - IDLE: No activity for 30s - 5min
    - AWAY: No activity for > 5min
    """

    id: str
    user_id: str
    study_id: str
    chapter_id: str | None
    move_path: str | None
    status: PresenceStatus
    last_heartbeat: datetime
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    # Timeout thresholds (in seconds)
    IDLE_THRESHOLD = 30
    AWAY_THRESHOLD = 300  # 5 minutes

    @property
    def cursor_position(self) -> CursorPosition | None:
        """Get the current cursor position if chapter is set."""
        if self.chapter_id:
            return CursorPosition(
                chapter_id=self.chapter_id,
                move_path=self.move_path
            )
        return None

    def update_heartbeat(
        self,
        chapter_id: str | None = None,
        move_path: str | None = None
    ) -> None:
        """
        Update the heartbeat timestamp and cursor position.

        Args:
            chapter_id: Optional chapter ID to update cursor position
            move_path: Optional move path to update cursor position
        """
        self.last_heartbeat = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)
        self.status = PresenceStatus.ACTIVE

        if chapter_id is not None:
            self.chapter_id = chapter_id
        if move_path is not None:
            self.move_path = move_path

    def update_status(self, elapsed_seconds: float) -> PresenceStatus:
        """
        Update status based on elapsed time since last heartbeat.

        Args:
            elapsed_seconds: Time elapsed since last heartbeat

        Returns:
            The new status
        """
        if elapsed_seconds < self.IDLE_THRESHOLD:
            new_status = PresenceStatus.ACTIVE
        elif elapsed_seconds < self.AWAY_THRESHOLD:
            new_status = PresenceStatus.IDLE
        else:
            new_status = PresenceStatus.AWAY

        if new_status != self.status:
            self.status = new_status
            self.updated_at = datetime.now(UTC)

        return self.status

    def is_expired(self, timeout_seconds: int = 600) -> bool:
        """
        Check if the session has expired (no heartbeat for timeout period).

        Default timeout is 10 minutes (600 seconds).

        Args:
            timeout_seconds: Timeout threshold in seconds

        Returns:
            True if session is expired, False otherwise
        """
        elapsed = (datetime.now(UTC) - self.last_heartbeat).total_seconds()
        return elapsed > timeout_seconds

    def time_since_last_heartbeat(self) -> float:
        """Get seconds since last heartbeat."""
        return (datetime.now(UTC) - self.last_heartbeat).total_seconds()
