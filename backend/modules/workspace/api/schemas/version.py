"""Version API schemas."""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class VersionSnapshotResponse(BaseModel):
    """Version snapshot response."""

    id: str
    version_id: str
    r2_key: str
    size_bytes: int | None
    content_hash: str | None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class StudyVersionResponse(BaseModel):
    """Study version response."""

    id: str
    study_id: str
    version_number: int
    created_by: str
    created_at: datetime
    change_summary: str | None = None
    is_rollback: bool = False
    snapshot: VersionSnapshotResponse | None = None


class VersionHistoryResponse(BaseModel):
    """Version history response."""

    versions: list[StudyVersionResponse]
    total_count: int
    has_more: bool


class VersionComparisonResponse(BaseModel):
    """Version comparison response."""

    from_version: int
    to_version: int
    changes: dict[str, Any]
    additions: list[dict[str, Any]] = Field(default_factory=list)
    deletions: list[dict[str, Any]] = Field(default_factory=list)
    modifications: list[dict[str, Any]] = Field(default_factory=list)


class CreateSnapshotRequest(BaseModel):
    """Create snapshot request."""

    change_summary: str | None = Field(
        None,
        description="Summary of changes in this version",
        max_length=500,
    )


class RollbackRequest(BaseModel):
    """Rollback request."""

    target_version: int = Field(
        ...,
        description="Version number to rollback to",
        ge=1,
    )
    reason: str | None = Field(
        None,
        description="Reason for rollback",
        max_length=500,
    )


class SnapshotContentResponse(BaseModel):
    """Snapshot content response (full study state)."""

    version_number: int
    study_id: str
    study_data: dict[str, Any]
    chapters: list[dict[str, Any]] = Field(default_factory=list)
    variations: list[dict[str, Any]] = Field(default_factory=list)
    annotations: list[dict[str, Any]] = Field(default_factory=list)
    timestamp: str
