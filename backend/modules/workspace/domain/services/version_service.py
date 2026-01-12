"""Version service for managing study versions and snapshots."""
import json
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from workspace.db.repos.version_repo import VersionRepository
from workspace.domain.models.version import (
    CreateVersionCommand,
    RollbackCommand,
    SnapshotContent,
    StudyVersion,
    VersionComparison,
    VersionSnapshot,
)
from workspace.events.bus import EventBus
from workspace.events.types import EventType
from workspace.storage.keys import R2Keys
from workspace.storage.r2_client import R2Client


class VersionService:
    """
    Service for version management.

    Handles:
    - Creating version snapshots
    - Comparing versions
    - Rolling back to previous versions
    - Version history management
    """

    def __init__(
        self,
        session: AsyncSession,
        r2_client: R2Client,
        event_bus: EventBus,
    ) -> None:
        """
        Initialize version service.

        Args:
            session: Database session
            r2_client: R2 storage client
            event_bus: Event bus for publishing events
        """
        self.session = session
        self.r2_client = r2_client
        self.event_bus = event_bus
        self.repo = VersionRepository(session)

    async def create_snapshot(
        self,
        command: CreateVersionCommand,
        snapshot_content: SnapshotContent,
    ) -> StudyVersion:
        """
        Create a new version snapshot.

        Args:
            command: Version creation command
            snapshot_content: Full study state to snapshot

        Returns:
            Created version

        Raises:
            ValueError: If snapshot creation fails
        """
        # Get next version number
        next_version = await self.repo.get_latest_version_number(command.study_id) + 1

        # Generate IDs
        version_id = str(uuid.uuid4())
        snapshot_id = str(uuid.uuid4())

        # Generate R2 key
        r2_key = R2Keys.version_snapshot(command.study_id, next_version)

        # Serialize snapshot content
        snapshot_dict = snapshot_content.to_dict()
        snapshot_json = json.dumps(snapshot_dict, indent=2)

        # Upload to R2
        upload_result = self.r2_client.upload_json(
            key=r2_key,
            content=snapshot_json,
            metadata={
                "version": str(next_version),
                "study_id": command.study_id,
                "created_by": command.created_by,
            },
        )

        # Create version record
        version = await self.repo.create_version(
            version_id=version_id,
            study_id=command.study_id,
            version_number=next_version,
            created_by=command.created_by,
            change_summary=command.change_summary,
            snapshot_key=r2_key,
            is_rollback=command.is_rollback,
        )

        # Create snapshot record
        snapshot = await self.repo.create_snapshot(
            snapshot_id=snapshot_id,
            version_id=version_id,
            r2_key=r2_key,
            size_bytes=upload_result.size,
            content_hash=upload_result.content_hash,
            metadata={
                "chapter_count": len(snapshot_content.chapters),
                "variation_count": len(snapshot_content.variations),
                "annotation_count": len(snapshot_content.annotations),
            },
        )

        await self.session.commit()

        # Publish event
        from workspace.domain.models.event import CreateEventCommand

        await self.event_bus.publish(
            CreateEventCommand(
                type=EventType.STUDY_SNAPSHOT_CREATED,
                actor_id=command.created_by,
                target_id=command.study_id,
                target_type="study",
                version=next_version,
                payload={
                    "version_number": next_version,
                    "change_summary": command.change_summary,
                    "is_rollback": command.is_rollback,
                    "snapshot_size": upload_result.size,
                },
                workspace_id=None,  # Will be set by caller
            )
        )

        # Build domain model
        return StudyVersion(
            id=version.id,
            study_id=version.study_id,
            version_number=version.version_number,
            created_by=version.created_by,
            created_at=version.created_at,
            change_summary=version.change_summary,
            snapshot_key=version.snapshot_key,
            is_rollback=version.is_rollback,
            snapshot=VersionSnapshot(
                id=snapshot.id,
                version_id=snapshot.version_id,
                r2_key=snapshot.r2_key,
                created_at=snapshot.created_at,
                size_bytes=snapshot.size_bytes,
                content_hash=snapshot.content_hash,
                metadata=snapshot.metadata or {},
            ),
        )

    async def get_version(
        self,
        study_id: str,
        version_number: int,
    ) -> StudyVersion | None:
        """
        Get a specific version.

        Args:
            study_id: Study ID
            version_number: Version number

        Returns:
            Version or None if not found
        """
        version_table = await self.repo.get_version_by_number(study_id, version_number)

        if version_table is None:
            return None

        # Get snapshot if exists
        snapshot_table = await self.repo.get_snapshot_by_version_id(version_table.id)

        snapshot = None
        if snapshot_table is not None:
            snapshot = VersionSnapshot(
                id=snapshot_table.id,
                version_id=snapshot_table.version_id,
                r2_key=snapshot_table.r2_key,
                created_at=snapshot_table.created_at,
                size_bytes=snapshot_table.size_bytes,
                content_hash=snapshot_table.content_hash,
                metadata=snapshot_table.metadata or {},
            )

        return StudyVersion(
            id=version_table.id,
            study_id=version_table.study_id,
            version_number=version_table.version_number,
            created_by=version_table.created_by,
            created_at=version_table.created_at,
            change_summary=version_table.change_summary,
            snapshot_key=version_table.snapshot_key,
            is_rollback=version_table.is_rollback,
            snapshot=snapshot,
        )

    async def get_snapshot_content(
        self,
        study_id: str,
        version_number: int,
    ) -> SnapshotContent | None:
        """
        Get snapshot content from R2.

        Args:
            study_id: Study ID
            version_number: Version number

        Returns:
            Snapshot content or None if not found
        """
        version = await self.get_version(study_id, version_number)

        if version is None or version.snapshot_key is None:
            return None

        # Download from R2
        try:
            snapshot_json = self.r2_client.download_json(version.snapshot_key)
            snapshot_dict = json.loads(snapshot_json)
            return SnapshotContent.from_dict(snapshot_dict)
        except Exception:
            return None

    async def get_version_history(
        self,
        study_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[StudyVersion]:
        """
        Get version history for a study.

        Args:
            study_id: Study ID
            limit: Maximum number of versions to return
            offset: Number of versions to skip

        Returns:
            List of versions (newest first)
        """
        version_tables = await self.repo.get_versions_by_study(
            study_id, limit=limit, offset=offset
        )

        versions = []
        for version_table in version_tables:
            # Get snapshot if exists
            snapshot_table = await self.repo.get_snapshot_by_version_id(
                version_table.id
            )

            snapshot = None
            if snapshot_table is not None:
                snapshot = VersionSnapshot(
                    id=snapshot_table.id,
                    version_id=snapshot_table.version_id,
                    r2_key=snapshot_table.r2_key,
                    created_at=snapshot_table.created_at,
                    size_bytes=snapshot_table.size_bytes,
                    content_hash=snapshot_table.content_hash,
                    metadata=snapshot_table.metadata or {},
                )

            versions.append(
                StudyVersion(
                    id=version_table.id,
                    study_id=version_table.study_id,
                    version_number=version_table.version_number,
                    created_by=version_table.created_by,
                    created_at=version_table.created_at,
                    change_summary=version_table.change_summary,
                    snapshot_key=version_table.snapshot_key,
                    is_rollback=version_table.is_rollback,
                    snapshot=snapshot,
                )
            )

        return versions

    async def compare_versions(
        self,
        study_id: str,
        from_version: int,
        to_version: int,
    ) -> VersionComparison:
        """
        Compare two versions.

        Args:
            study_id: Study ID
            from_version: Starting version number
            to_version: Ending version number

        Returns:
            Comparison result

        Raises:
            ValueError: If versions not found
        """
        # Get both snapshots
        from_snapshot = await self.get_snapshot_content(study_id, from_version)
        to_snapshot = await self.get_snapshot_content(study_id, to_version)

        if from_snapshot is None:
            raise ValueError(f"Version {from_version} not found")
        if to_snapshot is None:
            raise ValueError(f"Version {to_version} not found")

        # Calculate differences
        additions = []
        deletions = []
        modifications = []

        # Compare chapters
        from_chapter_ids = {ch["id"] for ch in from_snapshot.chapters}
        to_chapter_ids = {ch["id"] for ch in to_snapshot.chapters}

        # New chapters
        for chapter in to_snapshot.chapters:
            if chapter["id"] not in from_chapter_ids:
                additions.append({"type": "chapter", "data": chapter})

        # Deleted chapters
        for chapter in from_snapshot.chapters:
            if chapter["id"] not in to_chapter_ids:
                deletions.append({"type": "chapter", "data": chapter})

        # Modified chapters (simplified - compare titles)
        for to_chapter in to_snapshot.chapters:
            if to_chapter["id"] in from_chapter_ids:
                from_chapter = next(
                    ch for ch in from_snapshot.chapters if ch["id"] == to_chapter["id"]
                )
                if from_chapter != to_chapter:
                    modifications.append(
                        {
                            "type": "chapter",
                            "id": to_chapter["id"],
                            "from": from_chapter,
                            "to": to_chapter,
                        }
                    )

        # Compare variations
        from_var_ids = {v["id"] for v in from_snapshot.variations}
        to_var_ids = {v["id"] for v in to_snapshot.variations}

        for variation in to_snapshot.variations:
            if variation["id"] not in from_var_ids:
                additions.append({"type": "variation", "data": variation})

        for variation in from_snapshot.variations:
            if variation["id"] not in to_var_ids:
                deletions.append({"type": "variation", "data": variation})

        # Compare annotations
        from_ann_ids = {a["id"] for a in from_snapshot.annotations}
        to_ann_ids = {a["id"] for a in to_snapshot.annotations}

        for annotation in to_snapshot.annotations:
            if annotation["id"] not in from_ann_ids:
                additions.append({"type": "annotation", "data": annotation})

        for annotation in from_snapshot.annotations:
            if annotation["id"] not in to_ann_ids:
                deletions.append({"type": "annotation", "data": annotation})

        return VersionComparison(
            from_version=from_version,
            to_version=to_version,
            changes={
                "additions_count": len(additions),
                "deletions_count": len(deletions),
                "modifications_count": len(modifications),
            },
            additions=additions,
            deletions=deletions,
            modifications=modifications,
        )

    async def rollback(
        self,
        command: RollbackCommand,
    ) -> StudyVersion:
        """
        Rollback study to a previous version.

        Creates a new version that is a copy of the target version.

        Args:
            command: Rollback command

        Returns:
            New version created from rollback

        Raises:
            ValueError: If target version not found
        """
        # Get target version snapshot
        target_snapshot = await self.get_snapshot_content(
            command.study_id, command.target_version
        )

        if target_snapshot is None:
            raise ValueError(f"Version {command.target_version} not found")

        # Create new version with rollback flag
        change_summary = (
            f"Rollback to version {command.target_version}"
            if command.reason is None
            else f"Rollback to version {command.target_version}: {command.reason}"
        )

        version = await self.create_snapshot(
            command=CreateVersionCommand(
                study_id=command.study_id,
                created_by=command.user_id,
                change_summary=change_summary,
                is_rollback=True,
            ),
            snapshot_content=target_snapshot,
        )

        # Publish rollback event
        from workspace.domain.models.event import CreateEventCommand

        await self.event_bus.publish(
            CreateEventCommand(
                type=EventType.STUDY_ROLLBACK,
                actor_id=command.user_id,
                target_id=command.study_id,
                target_type="study",
                version=version.version_number,
                payload={
                    "new_version": version.version_number,
                    "target_version": command.target_version,
                    "reason": command.reason,
                },
                workspace_id=None,
            )
        )

        return version

    async def cleanup_old_versions(
        self,
        study_id: str,
        keep_count: int = 100,
    ) -> int:
        """
        Delete old versions beyond the keep limit.

        Args:
            study_id: Study ID
            keep_count: Number of recent versions to keep

        Returns:
            Number of deleted versions
        """
        deleted_count = await self.repo.delete_old_versions(study_id, keep_count)
        await self.session.commit()
        return deleted_count

    async def should_create_auto_snapshot(
        self,
        study_id: str,
        operation_count: int = 10,
        time_threshold_minutes: int = 5,
    ) -> bool:
        """
        Determine if an automatic snapshot should be created.

        Strategy:
        - Create snapshot every N operations
        - Create snapshot if no snapshot in last M minutes

        Args:
            study_id: Study ID
            operation_count: Number of operations since last snapshot
            time_threshold_minutes: Minutes since last snapshot

        Returns:
            True if snapshot should be created
        """
        # Get latest version
        latest_version_num = await self.repo.get_latest_version_number(study_id)

        if latest_version_num == 0:
            # No versions yet, create first snapshot
            return True

        latest_version = await self.get_version(study_id, latest_version_num)

        if latest_version is None:
            return True

        # Check time threshold
        time_since_last = datetime.now(UTC) - latest_version.created_at
        if time_since_last.total_seconds() > time_threshold_minutes * 60:
            return True

        # Check operation count threshold
        # This would require tracking operations, which we'll implement later
        # For now, just use time-based snapshots

        return False
