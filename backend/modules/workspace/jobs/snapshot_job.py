"""Periodic snapshot job for version history."""
import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from workspace.db.base import get_async_session_maker
from workspace.db.tables.studies import StudyTable
from workspace.domain.models.version import CreateVersionCommand, SnapshotContent
from workspace.domain.services.version_service import VersionService
from workspace.events.bus import EventBus
from workspace.storage.r2_client import create_r2_client_from_env

logger = logging.getLogger(__name__)


class SnapshotJob:
    """
    Background job for creating periodic version snapshots.

    Strategy:
    - Runs periodically (e.g., every 5 minutes)
    - Checks each study for auto-snapshot criteria
    - Creates snapshot if criteria met
    """

    def __init__(
        self,
        session_maker,
        r2_client,
        time_threshold_minutes: int = 5,
        operation_threshold: int = 10,
    ) -> None:
        """
        Initialize snapshot job.

        Args:
            session_maker: Database session maker
            r2_client: R2 storage client
            time_threshold_minutes: Create snapshot if no snapshot in this many minutes
            operation_threshold: Create snapshot after this many operations
        """
        self.session_maker = session_maker
        self.r2_client = r2_client
        self.time_threshold_minutes = time_threshold_minutes
        self.operation_threshold = operation_threshold

    async def run_once(self) -> dict[str, Any]:
        """
        Run snapshot job once.

        Returns:
            Job execution statistics
        """
        async with self.session_maker() as session:
            # Get all studies
            result = await session.execute(
                select(StudyTable)
                .where(StudyTable.deleted_at.is_(None))
                .limit(100)  # Process in batches
            )
            studies = result.scalars().all()

            stats = {
                "total_studies": len(studies),
                "snapshots_created": 0,
                "snapshots_skipped": 0,
                "errors": 0,
            }

            for study in studies:
                try:
                    created = await self._process_study(session, study.id, study.created_by)
                    if created:
                        stats["snapshots_created"] += 1
                    else:
                        stats["snapshots_skipped"] += 1
                except Exception as e:
                    logger.error(
                        f"Error processing study {study.id} for snapshot: {e}",
                        exc_info=True,
                    )
                    stats["errors"] += 1

            logger.info(
                f"Snapshot job completed: {stats['snapshots_created']} created, "
                f"{stats['snapshots_skipped']} skipped, {stats['errors']} errors"
            )

            return stats

    async def _process_study(
        self,
        session: AsyncSession,
        study_id: str,
        created_by: str,
    ) -> bool:
        """
        Process a single study for snapshot creation.

        Args:
            session: Database session
            study_id: Study ID
            created_by: User who created the study

        Returns:
            True if snapshot was created
        """
        event_bus = EventBus(session)
        version_service = VersionService(session, self.r2_client, event_bus)

        # Check if snapshot should be created
        should_create = await version_service.should_create_auto_snapshot(
            study_id=study_id,
            operation_count=self.operation_threshold,
            time_threshold_minutes=self.time_threshold_minutes,
        )

        if not should_create:
            return False

        # Get current study state
        # TODO: Implement proper study state capture
        # For now, create a minimal snapshot
        snapshot_content = SnapshotContent(
            version_number=0,  # Will be set by service
            study_id=study_id,
            study_data={"title": "Auto Snapshot"},  # Placeholder
            chapters=[],
            variations=[],
            annotations=[],
        )

        # Create snapshot
        await version_service.create_snapshot(
            command=CreateVersionCommand(
                study_id=study_id,
                created_by=created_by,
                change_summary="Automatic periodic snapshot",
                is_rollback=False,
            ),
            snapshot_content=snapshot_content,
        )

        logger.info(f"Created auto snapshot for study {study_id}")
        return True

    async def run_forever(self, interval_seconds: int = 300) -> None:
        """
        Run job continuously.

        Args:
            interval_seconds: Interval between runs (default: 5 minutes)
        """
        logger.info(
            f"Starting snapshot job with {interval_seconds}s interval, "
            f"{self.time_threshold_minutes}min time threshold"
        )

        while True:
            try:
                await self.run_once()
            except Exception as e:
                logger.error(f"Snapshot job failed: {e}", exc_info=True)

            await asyncio.sleep(interval_seconds)


async def create_snapshot_job_from_env() -> SnapshotJob:
    """
    Create snapshot job from environment configuration.

    Returns:
        Configured snapshot job
    """
    import os

    time_threshold = int(os.getenv("SNAPSHOT_TIME_THRESHOLD_MINUTES", "5"))
    operation_threshold = int(os.getenv("SNAPSHOT_OPERATION_THRESHOLD", "10"))

    session_maker = get_async_session_maker()
    r2_client = create_r2_client_from_env()

    return SnapshotJob(
        session_maker=session_maker,
        r2_client=r2_client,
        time_threshold_minutes=time_threshold,
        operation_threshold=operation_threshold,
    )


async def main() -> None:
    """Run snapshot job as standalone script."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    job = await create_snapshot_job_from_env()
    await job.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
