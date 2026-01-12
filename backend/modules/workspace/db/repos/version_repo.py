"""Version repository for database operations."""
from datetime import datetime
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from workspace.db.tables.study_versions import StudyVersionTable, VersionSnapshotTable


class VersionRepository:
    """Repository for version-related database operations."""

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize repository.

        Args:
            session: Database session
        """
        self.session = session

    async def create_version(
        self,
        version_id: str,
        study_id: str,
        version_number: int,
        created_by: str,
        change_summary: str | None = None,
        snapshot_key: str | None = None,
        is_rollback: bool = False,
    ) -> StudyVersionTable:
        """
        Create a new version record.

        Args:
            version_id: Version ID
            study_id: Study ID
            version_number: Version number
            created_by: User who created the version
            change_summary: Summary of changes
            snapshot_key: R2 key for snapshot
            is_rollback: Whether this is a rollback operation

        Returns:
            Created version record
        """
        version = StudyVersionTable(
            id=version_id,
            study_id=study_id,
            version_number=version_number,
            change_summary=change_summary,
            snapshot_key=snapshot_key,
            is_rollback=is_rollback,
            created_by=created_by,
        )
        self.session.add(version)
        await self.session.flush()
        return version

    async def create_snapshot(
        self,
        snapshot_id: str,
        version_id: str,
        r2_key: str,
        size_bytes: int | None = None,
        content_hash: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> VersionSnapshotTable:
        """
        Create a snapshot record.

        Args:
            snapshot_id: Snapshot ID
            version_id: Version ID
            r2_key: R2 storage key
            size_bytes: Size in bytes
            content_hash: Content hash
            metadata: Additional metadata

        Returns:
            Created snapshot record
        """
        snapshot = VersionSnapshotTable(
            id=snapshot_id,
            version_id=version_id,
            r2_key=r2_key,
            size_bytes=size_bytes,
            content_hash=content_hash,
            metadata=metadata,
        )
        self.session.add(snapshot)
        await self.session.flush()
        return snapshot

    async def get_version_by_id(self, version_id: str) -> StudyVersionTable | None:
        """
        Get version by ID.

        Args:
            version_id: Version ID

        Returns:
            Version record or None
        """
        result = await self.session.execute(
            select(StudyVersionTable).where(StudyVersionTable.id == version_id)
        )
        return result.scalar_one_or_none()

    async def get_version_by_number(
        self, study_id: str, version_number: int
    ) -> StudyVersionTable | None:
        """
        Get version by study ID and version number.

        Args:
            study_id: Study ID
            version_number: Version number

        Returns:
            Version record or None
        """
        result = await self.session.execute(
            select(StudyVersionTable).where(
                StudyVersionTable.study_id == study_id,
                StudyVersionTable.version_number == version_number,
            )
        )
        return result.scalar_one_or_none()

    async def get_latest_version_number(self, study_id: str) -> int:
        """
        Get the latest version number for a study.

        Args:
            study_id: Study ID

        Returns:
            Latest version number, or 0 if no versions exist
        """
        result = await self.session.execute(
            select(StudyVersionTable.version_number)
            .where(StudyVersionTable.study_id == study_id)
            .order_by(desc(StudyVersionTable.version_number))
            .limit(1)
        )
        version_number = result.scalar_one_or_none()
        return version_number if version_number is not None else 0

    async def get_versions_by_study(
        self,
        study_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[StudyVersionTable]:
        """
        Get version history for a study.

        Args:
            study_id: Study ID
            limit: Maximum number of versions to return
            offset: Number of versions to skip

        Returns:
            List of version records
        """
        result = await self.session.execute(
            select(StudyVersionTable)
            .where(StudyVersionTable.study_id == study_id)
            .order_by(desc(StudyVersionTable.version_number))
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def get_snapshot_by_version_id(
        self, version_id: str
    ) -> VersionSnapshotTable | None:
        """
        Get snapshot by version ID.

        Args:
            version_id: Version ID

        Returns:
            Snapshot record or None
        """
        result = await self.session.execute(
            select(VersionSnapshotTable).where(
                VersionSnapshotTable.version_id == version_id
            )
        )
        return result.scalar_one_or_none()

    async def delete_old_versions(
        self, study_id: str, keep_count: int = 100
    ) -> int:
        """
        Delete old versions, keeping only the most recent ones.

        Args:
            study_id: Study ID
            keep_count: Number of versions to keep

        Returns:
            Number of deleted versions
        """
        # Get version numbers to delete
        result = await self.session.execute(
            select(StudyVersionTable.id)
            .where(StudyVersionTable.study_id == study_id)
            .order_by(desc(StudyVersionTable.version_number))
            .offset(keep_count)
        )
        version_ids = [row[0] for row in result.all()]

        if not version_ids:
            return 0

        # Delete versions (snapshots will cascade delete)
        from sqlalchemy import delete as sa_delete

        await self.session.execute(
            sa_delete(StudyVersionTable).where(StudyVersionTable.id.in_(version_ids))
        )

        return len(version_ids)
