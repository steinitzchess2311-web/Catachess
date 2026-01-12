"""
Presence cleanup background job.

Periodically cleans up expired presence sessions to prevent
database bloat and maintain accurate online user counts.
"""

import asyncio
import logging
from datetime import timedelta

from workspace.domain.services.presence_service import PresenceService

logger = logging.getLogger(__name__)


class PresenceCleanupJob:
    """
    Background job for cleaning up expired presence sessions.

    This job should run periodically (e.g., every 5 minutes) to:
    1. Remove sessions with no heartbeat for > timeout period
    2. Publish user_left events for expired sessions
    3. Keep the database clean

    Recommended schedule: Every 5 minutes
    Default timeout: 10 minutes (sessions expire after 10min of no heartbeat)
    """

    def __init__(
        self,
        presence_service: PresenceService,
        timeout_minutes: int = 10,
        interval_seconds: int = 300,  # 5 minutes
    ):
        """
        Initialize cleanup job.

        Args:
            presence_service: Presence service instance
            timeout_minutes: Session timeout in minutes (default: 10)
            interval_seconds: Cleanup interval in seconds (default: 300 = 5min)
        """
        self.presence_service = presence_service
        self.timeout_minutes = timeout_minutes
        self.interval_seconds = interval_seconds
        self._running = False
        self._task = None

    async def run_once(self) -> int:
        """
        Run cleanup once.

        Returns:
            Number of sessions cleaned up
        """
        try:
            count = await self.presence_service.cleanup_expired_sessions(
                timeout_minutes=self.timeout_minutes
            )

            if count > 0:
                logger.info(f"Presence cleanup: removed {count} expired sessions")
            else:
                logger.debug("Presence cleanup: no expired sessions found")

            return count

        except Exception as e:
            logger.error(f"Error in presence cleanup job: {e}", exc_info=True)
            return 0

    async def run_forever(self):
        """
        Run cleanup job forever (until stopped).

        This method runs an infinite loop, cleaning up expired sessions
        at regular intervals.
        """
        logger.info(
            f"Starting presence cleanup job "
            f"(interval={self.interval_seconds}s, timeout={self.timeout_minutes}min)"
        )

        self._running = True

        while self._running:
            try:
                await self.run_once()
                await asyncio.sleep(self.interval_seconds)

            except asyncio.CancelledError:
                logger.info("Presence cleanup job cancelled")
                break
            except Exception as e:
                logger.error(f"Error in presence cleanup loop: {e}", exc_info=True)
                # Sleep a bit before retrying to avoid tight error loop
                await asyncio.sleep(30)

        logger.info("Presence cleanup job stopped")

    def start(self):
        """
        Start the cleanup job in the background.

        Returns:
            asyncio.Task: The background task
        """
        if self._task is not None and not self._task.done():
            logger.warning("Presence cleanup job already running")
            return self._task

        self._task = asyncio.create_task(self.run_forever())
        return self._task

    async def stop(self):
        """
        Stop the cleanup job.

        Waits for the current cleanup to finish before stopping.
        """
        if self._task is None:
            logger.warning("Presence cleanup job not running")
            return

        logger.info("Stopping presence cleanup job...")
        self._running = False

        if not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        self._task = None
        logger.info("Presence cleanup job stopped")


# Example usage for standalone execution
async def main():
    """
    Example standalone execution of presence cleanup job.

    In production, this would be integrated with your application's
    lifecycle management (e.g., FastAPI lifespan events).
    """
    # This is a placeholder - in production you'd properly initialize
    # the database session and services
    from workspace.db.base import get_session
    from workspace.db.repos.presence_repo import PresenceRepository
    from workspace.events.bus import EventBus

    async with get_session() as session:
        presence_repo = PresenceRepository(session)
        event_bus = EventBus()  # Properly initialize in production
        presence_service = PresenceService(
            session=session,
            presence_repo=presence_repo,
            event_bus=event_bus
        )

        job = PresenceCleanupJob(
            presence_service=presence_service,
            timeout_minutes=10,
            interval_seconds=300,
        )

        try:
            await job.run_forever()
        except KeyboardInterrupt:
            await job.stop()


if __name__ == "__main__":
    asyncio.run(main())
