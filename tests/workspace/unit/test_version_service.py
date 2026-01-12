"""Unit tests for version service."""
import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from workspace.domain.models.version import (
    CreateVersionCommand,
    RollbackCommand,
    SnapshotContent,
)
from workspace.domain.services.version_service import VersionService
from workspace.events.bus import EventBus
from workspace.storage.r2_client import R2Client, UploadResult


@pytest.fixture
def mock_session():
    """Create mock database session."""
    session = MagicMock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.flush = AsyncMock()
    return session


@pytest.fixture
def mock_r2_client():
    """Create mock R2 client."""
    client = MagicMock(spec=R2Client)
    client.upload_json = MagicMock(
        return_value=UploadResult(
            key="snapshots/study_1/1.json",
            etag="abc123",
            size=1024,
            content_hash="hash123",
        )
    )
    client.download_json = MagicMock(
        return_value=json.dumps(
            {
                "version_number": 1,
                "study_id": "study_1",
                "study_data": {"title": "Test Study"},
                "chapters": [{"id": "ch1", "title": "Chapter 1"}],
                "variations": [],
                "annotations": [],
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )
    )
    return client


@pytest.fixture
def mock_event_bus():
    """Create mock event bus."""
    bus = MagicMock(spec=EventBus)
    bus.publish = AsyncMock()
    return bus


@pytest.fixture
def version_service(mock_session, mock_r2_client, mock_event_bus):
    """Create version service with mocks."""
    return VersionService(mock_session, mock_r2_client, mock_event_bus)


@pytest.mark.asyncio
async def test_create_snapshot(version_service, mock_r2_client):
    """Test creating a version snapshot."""
    # Prepare
    command = CreateVersionCommand(
        study_id="study_1",
        created_by="user_1",
        change_summary="Test snapshot",
    )

    snapshot_content = SnapshotContent(
        version_number=0,
        study_id="study_1",
        study_data={"title": "Test Study"},
        chapters=[{"id": "ch1", "title": "Chapter 1"}],
        variations=[],
        annotations=[],
    )

    # Mock repository methods
    with patch.object(
        version_service.repo, "get_latest_version_number", return_value=0
    ):
        with patch.object(
            version_service.repo,
            "create_version",
            return_value=MagicMock(
                id="v1",
                study_id="study_1",
                version_number=1,
                created_by="user_1",
                created_at=datetime.now(UTC),
                change_summary="Test snapshot",
                snapshot_key="snapshots/study_1/1.json",
                is_rollback=False,
            ),
        ):
            with patch.object(
                version_service.repo,
                "create_snapshot",
                return_value=MagicMock(
                    id="s1",
                    version_id="v1",
                    r2_key="snapshots/study_1/1.json",
                    size_bytes=1024,
                    content_hash="hash123",
                    metadata={},
                    created_at=datetime.now(UTC),
                ),
            ):
                # Act
                version = await version_service.create_snapshot(command, snapshot_content)

    # Assert
    assert version.study_id == "study_1"
    assert version.version_number == 1
    assert version.created_by == "user_1"
    assert version.change_summary == "Test snapshot"
    assert version.is_rollback is False
    assert version.snapshot is not None

    # Verify R2 upload was called
    mock_r2_client.upload_json.assert_called_once()


@pytest.mark.asyncio
async def test_get_version(version_service):
    """Test getting a specific version."""
    # Mock repository
    mock_version = MagicMock(
        id="v1",
        study_id="study_1",
        version_number=1,
        created_by="user_1",
        created_at=datetime.now(UTC),
        change_summary="Test",
        snapshot_key="key",
        is_rollback=False,
    )

    with patch.object(
        version_service.repo, "get_version_by_number", return_value=mock_version
    ):
        with patch.object(version_service.repo, "get_snapshot_by_version_id", return_value=None):
            # Act
            version = await version_service.get_version("study_1", 1)

    # Assert
    assert version is not None
    assert version.version_number == 1
    assert version.study_id == "study_1"


@pytest.mark.asyncio
async def test_get_version_not_found(version_service):
    """Test getting a non-existent version."""
    with patch.object(version_service.repo, "get_version_by_number", return_value=None):
        # Act
        version = await version_service.get_version("study_1", 999)

    # Assert
    assert version is None


@pytest.mark.asyncio
async def test_get_version_history(version_service):
    """Test getting version history."""
    # Mock repository
    mock_versions = [
        MagicMock(
            id=f"v{i}",
            study_id="study_1",
            version_number=i,
            created_by="user_1",
            created_at=datetime.now(UTC),
            change_summary=f"Version {i}",
            snapshot_key=f"key{i}",
            is_rollback=False,
        )
        for i in range(1, 4)
    ]

    with patch.object(
        version_service.repo, "get_versions_by_study", return_value=mock_versions
    ):
        with patch.object(version_service.repo, "get_snapshot_by_version_id", return_value=None):
            # Act
            versions = await version_service.get_version_history("study_1", limit=10)

    # Assert
    assert len(versions) == 3
    assert versions[0].version_number == 1
    assert versions[2].version_number == 3


@pytest.mark.asyncio
async def test_compare_versions(version_service, mock_r2_client):
    """Test comparing two versions."""
    # Mock R2 responses with different content
    mock_r2_client.download_json.side_effect = [
        json.dumps(
            {
                "version_number": 1,
                "study_id": "study_1",
                "study_data": {"title": "Test Study V1"},
                "chapters": [{"id": "ch1", "title": "Chapter 1"}],
                "variations": [],
                "annotations": [],
                "timestamp": datetime.now(UTC).isoformat(),
            }
        ),
        json.dumps(
            {
                "version_number": 2,
                "study_id": "study_1",
                "study_data": {"title": "Test Study V2"},
                "chapters": [
                    {"id": "ch1", "title": "Chapter 1 Updated"},
                    {"id": "ch2", "title": "Chapter 2"},
                ],
                "variations": [{"id": "var1", "move": "e4"}],
                "annotations": [],
                "timestamp": datetime.now(UTC).isoformat(),
            }
        ),
    ]

    # Mock get_version
    async def mock_get_version(study_id, version_number):
        return MagicMock(
            study_id=study_id,
            version_number=version_number,
            snapshot_key=f"key{version_number}",
        )

    with patch.object(version_service, "get_version", side_effect=mock_get_version):
        # Act
        comparison = await version_service.compare_versions("study_1", 1, 2)

    # Assert
    assert comparison.from_version == 1
    assert comparison.to_version == 2
    assert comparison.changes["additions_count"] > 0
    assert len(comparison.additions) > 0


@pytest.mark.asyncio
async def test_rollback(version_service, mock_r2_client):
    """Test rolling back to a previous version."""
    # Mock get_snapshot_content
    snapshot_content = SnapshotContent(
        version_number=1,
        study_id="study_1",
        study_data={"title": "Test Study"},
        chapters=[],
        variations=[],
        annotations=[],
    )

    with patch.object(
        version_service, "get_snapshot_content", return_value=snapshot_content
    ):
        with patch.object(
            version_service, "create_snapshot", return_value=MagicMock(version_number=3)
        ):
            # Act
            command = RollbackCommand(
                study_id="study_1",
                target_version=1,
                user_id="user_1",
                reason="Test rollback",
            )

            version = await version_service.rollback(command)

    # Assert
    assert version.version_number == 3  # New version created


@pytest.mark.asyncio
async def test_rollback_to_nonexistent_version(version_service):
    """Test rolling back to a non-existent version."""
    with patch.object(version_service, "get_snapshot_content", return_value=None):
        # Act & Assert
        with pytest.raises(ValueError, match="Version 999 not found"):
            await version_service.rollback(
                RollbackCommand(
                    study_id="study_1",
                    target_version=999,
                    user_id="user_1",
                )
            )


@pytest.mark.asyncio
async def test_should_create_auto_snapshot_first_time(version_service):
    """Test auto snapshot should be created for first time."""
    with patch.object(version_service.repo, "get_latest_version_number", return_value=0):
        # Act
        should_create = await version_service.should_create_auto_snapshot("study_1")

    # Assert
    assert should_create is True


@pytest.mark.asyncio
async def test_should_create_auto_snapshot_time_threshold(version_service):
    """Test auto snapshot based on time threshold."""
    # Mock old version
    old_version = MagicMock(
        created_at=datetime(2020, 1, 1, tzinfo=UTC),  # Old timestamp
    )

    with patch.object(version_service.repo, "get_latest_version_number", return_value=1):
        with patch.object(version_service, "get_version", return_value=old_version):
            # Act
            should_create = await version_service.should_create_auto_snapshot(
                "study_1", time_threshold_minutes=5
            )

    # Assert
    assert should_create is True


@pytest.mark.asyncio
async def test_should_not_create_auto_snapshot_recent(version_service):
    """Test auto snapshot should not be created if recent snapshot exists."""
    # Mock recent version
    recent_version = MagicMock(
        created_at=datetime.now(UTC),  # Just now
    )

    with patch.object(version_service.repo, "get_latest_version_number", return_value=1):
        with patch.object(version_service, "get_version", return_value=recent_version):
            # Act
            should_create = await version_service.should_create_auto_snapshot(
                "study_1", time_threshold_minutes=5
            )

    # Assert
    assert should_create is False


@pytest.mark.asyncio
async def test_cleanup_old_versions(version_service):
    """Test cleaning up old versions."""
    with patch.object(version_service.repo, "delete_old_versions", return_value=10):
        # Act
        deleted_count = await version_service.cleanup_old_versions("study_1", keep_count=50)

    # Assert
    assert deleted_count == 10
