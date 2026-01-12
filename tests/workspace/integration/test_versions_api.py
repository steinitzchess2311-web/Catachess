"""Integration tests for version API endpoints."""
import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from workspace.api.main import create_app
from workspace.domain.models.version import SnapshotContent, StudyVersion, VersionSnapshot
from workspace.storage.r2_client import UploadResult


@pytest.fixture
def app():
    """Create FastAPI app for testing."""
    return create_app()


@pytest.fixture
async def client(app):
    """Create async HTTP client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_version_service():
    """Create mock version service."""
    service = MagicMock()

    # Mock methods
    service.get_version_history = AsyncMock(
        return_value=[
            StudyVersion(
                id=f"v{i}",
                study_id="study_1",
                version_number=i,
                created_by="user_1",
                created_at=datetime(2026, 1, 12, 10, i, 0, tzinfo=UTC),
                change_summary=f"Version {i}",
                is_rollback=False,
                snapshot=VersionSnapshot(
                    id=f"s{i}",
                    version_id=f"v{i}",
                    r2_key=f"snapshots/study_1/{i}.json",
                    created_at=datetime(2026, 1, 12, 10, i, 0, tzinfo=UTC),
                    size_bytes=1024,
                    content_hash="hash123",
                ),
            )
            for i in range(1, 4)
        ]
    )

    service.get_version = AsyncMock(
        return_value=StudyVersion(
            id="v1",
            study_id="study_1",
            version_number=1,
            created_by="user_1",
            created_at=datetime(2026, 1, 12, 10, 0, 0, tzinfo=UTC),
            change_summary="Version 1",
            is_rollback=False,
            snapshot=VersionSnapshot(
                id="s1",
                version_id="v1",
                r2_key="snapshots/study_1/1.json",
                created_at=datetime(2026, 1, 12, 10, 0, 0, tzinfo=UTC),
                size_bytes=1024,
                content_hash="hash123",
            ),
        )
    )

    service.get_snapshot_content = AsyncMock(
        return_value=SnapshotContent(
            version_number=1,
            study_id="study_1",
            study_data={"title": "Test Study"},
            chapters=[{"id": "ch1", "title": "Chapter 1"}],
            variations=[],
            annotations=[],
        )
    )

    service.compare_versions = AsyncMock()
    service.create_snapshot = AsyncMock()
    service.rollback = AsyncMock()

    return service


@pytest.mark.asyncio
async def test_get_version_history(client, mock_version_service):
    """Test GET /studies/{id}/versions endpoint."""
    with patch(
        "workspace.api.endpoints.versions.get_version_service",
        return_value=mock_version_service,
    ):
        # Act
        response = await client.get("/studies/study_1/versions")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "versions" in data
    assert len(data["versions"]) == 3
    assert data["versions"][0]["version_number"] == 1
    assert data["versions"][0]["study_id"] == "study_1"
    assert "snapshot" in data["versions"][0]


@pytest.mark.asyncio
async def test_get_version_history_with_pagination(client, mock_version_service):
    """Test version history with pagination."""
    with patch(
        "workspace.api.endpoints.versions.get_version_service",
        return_value=mock_version_service,
    ):
        # Act
        response = await client.get("/studies/study_1/versions?limit=2&offset=1")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "versions" in data
    # Service was called with limit+1 to check for more results
    mock_version_service.get_version_history.assert_called_once()


@pytest.mark.asyncio
async def test_get_specific_version(client, mock_version_service):
    """Test GET /studies/{id}/versions/{version_number} endpoint."""
    with patch(
        "workspace.api.endpoints.versions.get_version_service",
        return_value=mock_version_service,
    ):
        # Act
        response = await client.get("/studies/study_1/versions/1")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["version_number"] == 1
    assert data["study_id"] == "study_1"
    assert data["change_summary"] == "Version 1"
    assert data["snapshot"] is not None


@pytest.mark.asyncio
async def test_get_version_not_found(client, mock_version_service):
    """Test getting non-existent version."""
    mock_version_service.get_version = AsyncMock(return_value=None)

    with patch(
        "workspace.api.endpoints.versions.get_version_service",
        return_value=mock_version_service,
    ):
        # Act
        response = await client.get("/studies/study_1/versions/999")

    # Assert
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_snapshot_content(client, mock_version_service):
    """Test GET /studies/{id}/versions/{version}/content endpoint."""
    with patch(
        "workspace.api.endpoints.versions.get_version_service",
        return_value=mock_version_service,
    ):
        # Act
        response = await client.get("/studies/study_1/versions/1/content")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["version_number"] == 1
    assert data["study_id"] == "study_1"
    assert "study_data" in data
    assert "chapters" in data
    assert len(data["chapters"]) == 1


@pytest.mark.asyncio
async def test_get_snapshot_content_not_found(client, mock_version_service):
    """Test getting snapshot content for non-existent version."""
    mock_version_service.get_snapshot_content = AsyncMock(return_value=None)

    with patch(
        "workspace.api.endpoints.versions.get_version_service",
        return_value=mock_version_service,
    ):
        # Act
        response = await client.get("/studies/study_1/versions/999/content")

    # Assert
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_compare_versions(client, mock_version_service):
    """Test GET /studies/{id}/versions/{v}/diff endpoint."""
    from workspace.domain.models.version import VersionComparison

    mock_version_service.compare_versions = AsyncMock(
        return_value=VersionComparison(
            from_version=1,
            to_version=2,
            changes={"additions_count": 1, "deletions_count": 0, "modifications_count": 1},
            additions=[{"type": "chapter", "data": {"id": "ch2", "title": "Chapter 2"}}],
            deletions=[],
            modifications=[{"type": "chapter", "id": "ch1", "from": {}, "to": {}}],
        )
    )

    with patch(
        "workspace.api.endpoints.versions.get_version_service",
        return_value=mock_version_service,
    ):
        # Act
        response = await client.get("/studies/study_1/versions/1/diff?compare_with=2")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["from_version"] == 1
    assert data["to_version"] == 2
    assert data["changes"]["additions_count"] == 1
    assert len(data["additions"]) == 1


@pytest.mark.asyncio
async def test_compare_versions_not_found(client, mock_version_service):
    """Test comparing with non-existent version."""
    mock_version_service.compare_versions = AsyncMock(side_effect=ValueError("Version not found"))

    with patch(
        "workspace.api.endpoints.versions.get_version_service",
        return_value=mock_version_service,
    ):
        # Act
        response = await client.get("/studies/study_1/versions/1/diff?compare_with=999")

    # Assert
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_manual_snapshot(client, mock_version_service):
    """Test POST /studies/{id}/versions endpoint."""
    mock_version_service.create_snapshot = AsyncMock(
        return_value=StudyVersion(
            id="v2",
            study_id="study_1",
            version_number=2,
            created_by="user_test",
            created_at=datetime.now(UTC),
            change_summary="Manual snapshot",
            is_rollback=False,
            snapshot=VersionSnapshot(
                id="s2",
                version_id="v2",
                r2_key="snapshots/study_1/2.json",
                created_at=datetime.now(UTC),
                size_bytes=1024,
                content_hash="hash123",
            ),
        )
    )

    with patch(
        "workspace.api.endpoints.versions.get_version_service",
        return_value=mock_version_service,
    ):
        # Act
        response = await client.post(
            "/studies/study_1/versions",
            json={"change_summary": "Manual snapshot"},
        )

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["version_number"] == 2
    assert data["change_summary"] == "Manual snapshot"
    assert data["is_rollback"] is False


@pytest.mark.asyncio
async def test_rollback_to_version(client, mock_version_service):
    """Test POST /studies/{id}/rollback endpoint."""
    mock_version_service.rollback = AsyncMock(
        return_value=StudyVersion(
            id="v3",
            study_id="study_1",
            version_number=3,
            created_by="user_test",
            created_at=datetime.now(UTC),
            change_summary="Rollback to version 1",
            is_rollback=True,
            snapshot=VersionSnapshot(
                id="s3",
                version_id="v3",
                r2_key="snapshots/study_1/3.json",
                created_at=datetime.now(UTC),
                size_bytes=1024,
                content_hash="hash123",
            ),
        )
    )

    with patch(
        "workspace.api.endpoints.versions.get_version_service",
        return_value=mock_version_service,
    ):
        # Act
        response = await client.post(
            "/studies/study_1/rollback",
            json={"target_version": 1, "reason": "Test rollback"},
        )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["version_number"] == 3
    assert data["is_rollback"] is True
    assert "Rollback to version 1" in data["change_summary"]


@pytest.mark.asyncio
async def test_rollback_to_nonexistent_version(client, mock_version_service):
    """Test rollback to non-existent version."""
    mock_version_service.rollback = AsyncMock(side_effect=ValueError("Version 999 not found"))

    with patch(
        "workspace.api.endpoints.versions.get_version_service",
        return_value=mock_version_service,
    ):
        # Act
        response = await client.post(
            "/studies/study_1/rollback",
            json={"target_version": 999},
        )

    # Assert
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_rollback_with_invalid_version_number(client):
    """Test rollback with invalid version number (< 1)."""
    # Act
    response = await client.post(
        "/studies/study_1/rollback",
        json={"target_version": 0},  # Invalid: must be >= 1
    )

    # Assert
    assert response.status_code == 422  # Validation error
