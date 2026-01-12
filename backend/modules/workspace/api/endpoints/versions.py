"""Version management API endpoints."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from workspace.api.schemas.version import (
    CreateSnapshotRequest,
    RollbackRequest,
    SnapshotContentResponse,
    StudyVersionResponse,
    VersionComparisonResponse,
    VersionHistoryResponse,
    VersionSnapshotResponse,
)
from workspace.db.base import get_session
from workspace.domain.models.version import (
    CreateVersionCommand,
    RollbackCommand,
    SnapshotContent,
)
from workspace.domain.services.version_service import VersionService
from workspace.events.bus import EventBus
from workspace.storage.r2_client import create_r2_client_from_env

router = APIRouter(prefix="/studies", tags=["versions"])


async def get_version_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> VersionService:
    """Dependency for version service."""
    r2_client = create_r2_client_from_env()
    event_bus = EventBus(session)
    return VersionService(session, r2_client, event_bus)


@router.get("/{study_id}/versions", response_model=VersionHistoryResponse)
async def get_version_history(
    study_id: str,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    version_service: Annotated[VersionService, Depends(get_version_service)],
) -> VersionHistoryResponse:
    """
    Get version history for a study.

    Args:
        study_id: Study ID
        limit: Maximum number of versions to return
        offset: Number of versions to skip
        version_service: Version service

    Returns:
        Version history response
    """
    versions = await version_service.get_version_history(
        study_id=study_id,
        limit=limit + 1,  # Get one extra to check if there are more
        offset=offset,
    )

    has_more = len(versions) > limit
    if has_more:
        versions = versions[:limit]

    # Convert to response models
    version_responses = []
    for version in versions:
        snapshot_response = None
        if version.snapshot is not None:
            snapshot_response = VersionSnapshotResponse(
                id=version.snapshot.id,
                version_id=version.snapshot.version_id,
                r2_key=version.snapshot.r2_key,
                size_bytes=version.snapshot.size_bytes,
                content_hash=version.snapshot.content_hash,
                metadata=version.snapshot.metadata,
                created_at=version.snapshot.created_at,
            )

        version_responses.append(
            StudyVersionResponse(
                id=version.id,
                study_id=version.study_id,
                version_number=version.version_number,
                created_by=version.created_by,
                created_at=version.created_at,
                change_summary=version.change_summary,
                is_rollback=version.is_rollback,
                snapshot=snapshot_response,
            )
        )

    return VersionHistoryResponse(
        versions=version_responses,
        total_count=len(version_responses),
        has_more=has_more,
    )


@router.get("/{study_id}/versions/{version_number}", response_model=StudyVersionResponse)
async def get_version(
    study_id: str,
    version_number: int,
    version_service: Annotated[VersionService, Depends(get_version_service)],
) -> StudyVersionResponse:
    """
    Get a specific version.

    Args:
        study_id: Study ID
        version_number: Version number
        version_service: Version service

    Returns:
        Version response

    Raises:
        HTTPException: If version not found
    """
    version = await version_service.get_version(study_id, version_number)

    if version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version {version_number} not found for study {study_id}",
        )

    snapshot_response = None
    if version.snapshot is not None:
        snapshot_response = VersionSnapshotResponse(
            id=version.snapshot.id,
            version_id=version.snapshot.version_id,
            r2_key=version.snapshot.r2_key,
            size_bytes=version.snapshot.size_bytes,
            content_hash=version.snapshot.content_hash,
            metadata=version.snapshot.metadata,
            created_at=version.snapshot.created_at,
        )

    return StudyVersionResponse(
        id=version.id,
        study_id=version.study_id,
        version_number=version.version_number,
        created_by=version.created_by,
        created_at=version.created_at,
        change_summary=version.change_summary,
        is_rollback=version.is_rollback,
        snapshot=snapshot_response,
    )


@router.get("/{study_id}/versions/{version_number}/content", response_model=SnapshotContentResponse)
async def get_snapshot_content(
    study_id: str,
    version_number: int,
    version_service: Annotated[VersionService, Depends(get_version_service)],
) -> SnapshotContentResponse:
    """
    Get full snapshot content for a version.

    Args:
        study_id: Study ID
        version_number: Version number
        version_service: Version service

    Returns:
        Snapshot content

    Raises:
        HTTPException: If snapshot not found
    """
    snapshot = await version_service.get_snapshot_content(study_id, version_number)

    if snapshot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Snapshot for version {version_number} not found",
        )

    return SnapshotContentResponse(
        version_number=snapshot.version_number,
        study_id=snapshot.study_id,
        study_data=snapshot.study_data,
        chapters=snapshot.chapters,
        variations=snapshot.variations,
        annotations=snapshot.annotations,
        timestamp=snapshot.timestamp.isoformat(),
    )


@router.get("/{study_id}/versions/{version_number}/diff", response_model=VersionComparisonResponse)
async def compare_versions(
    study_id: str,
    version_number: int,
    compare_with: int = Query(..., description="Version to compare with"),
    version_service: Annotated[VersionService, Depends(get_version_service)],
) -> VersionComparisonResponse:
    """
    Compare two versions.

    Args:
        study_id: Study ID
        version_number: First version number
        compare_with: Second version number
        version_service: Version service

    Returns:
        Version comparison

    Raises:
        HTTPException: If comparison fails
    """
    try:
        comparison = await version_service.compare_versions(
            study_id=study_id,
            from_version=version_number,
            to_version=compare_with,
        )

        return VersionComparisonResponse(
            from_version=comparison.from_version,
            to_version=comparison.to_version,
            changes=comparison.changes,
            additions=comparison.additions,
            deletions=comparison.deletions,
            modifications=comparison.modifications,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/{study_id}/versions", response_model=StudyVersionResponse, status_code=status.HTTP_201_CREATED)
async def create_manual_snapshot(
    study_id: str,
    request: CreateSnapshotRequest,
    version_service: Annotated[VersionService, Depends(get_version_service)],
    # TODO: Add current_user dependency
) -> StudyVersionResponse:
    """
    Create a manual snapshot.

    Args:
        study_id: Study ID
        request: Create snapshot request
        version_service: Version service

    Returns:
        Created version

    Raises:
        HTTPException: If snapshot creation fails
    """
    # TODO: Get current user from auth
    user_id = "user_test"  # Placeholder

    # TODO: Get current study state
    # For now, create a minimal snapshot
    snapshot_content = SnapshotContent(
        version_number=0,  # Will be set by service
        study_id=study_id,
        study_data={"title": "Test Study"},  # Placeholder
        chapters=[],
        variations=[],
        annotations=[],
    )

    try:
        version = await version_service.create_snapshot(
            command=CreateVersionCommand(
                study_id=study_id,
                created_by=user_id,
                change_summary=request.change_summary,
                is_rollback=False,
            ),
            snapshot_content=snapshot_content,
        )

        snapshot_response = None
        if version.snapshot is not None:
            snapshot_response = VersionSnapshotResponse(
                id=version.snapshot.id,
                version_id=version.snapshot.version_id,
                r2_key=version.snapshot.r2_key,
                size_bytes=version.snapshot.size_bytes,
                content_hash=version.snapshot.content_hash,
                metadata=version.snapshot.metadata,
                created_at=version.snapshot.created_at,
            )

        return StudyVersionResponse(
            id=version.id,
            study_id=version.study_id,
            version_number=version.version_number,
            created_by=version.created_by,
            created_at=version.created_at,
            change_summary=version.change_summary,
            is_rollback=version.is_rollback,
            snapshot=snapshot_response,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create snapshot: {str(e)}",
        )


@router.post("/{study_id}/rollback", response_model=StudyVersionResponse)
async def rollback_to_version(
    study_id: str,
    request: RollbackRequest,
    version_service: Annotated[VersionService, Depends(get_version_service)],
    # TODO: Add current_user dependency
) -> StudyVersionResponse:
    """
    Rollback study to a previous version.

    Args:
        study_id: Study ID
        request: Rollback request
        version_service: Version service

    Returns:
        New version created from rollback

    Raises:
        HTTPException: If rollback fails
    """
    # TODO: Get current user from auth
    user_id = "user_test"  # Placeholder

    try:
        version = await version_service.rollback(
            command=RollbackCommand(
                study_id=study_id,
                target_version=request.target_version,
                user_id=user_id,
                reason=request.reason,
            )
        )

        snapshot_response = None
        if version.snapshot is not None:
            snapshot_response = VersionSnapshotResponse(
                id=version.snapshot.id,
                version_id=version.snapshot.version_id,
                r2_key=version.snapshot.r2_key,
                size_bytes=version.snapshot.size_bytes,
                content_hash=version.snapshot.content_hash,
                metadata=version.snapshot.metadata,
                created_at=version.snapshot.created_at,
            )

        return StudyVersionResponse(
            id=version.id,
            study_id=version.study_id,
            version_number=version.version_number,
            created_by=version.created_by,
            created_at=version.created_at,
            change_summary=version.change_summary,
            is_rollback=version.is_rollback,
            snapshot=snapshot_response,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rollback: {str(e)}",
        )
