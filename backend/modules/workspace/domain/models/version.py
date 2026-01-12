"""Version domain models."""
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class StudyVersion:
    """
    Study version aggregate root.

    Represents a version snapshot of a study at a specific point in time.
    """

    id: str
    study_id: str
    version_number: int
    created_by: str
    created_at: datetime
    change_summary: str | None = None
    snapshot_key: str | None = None
    is_rollback: bool = False
    snapshot: "VersionSnapshot | None" = None

    def __post_init__(self) -> None:
        """Validate version after initialization."""
        if self.version_number < 1:
            raise ValueError("Version number must be >= 1")


@dataclass
class VersionSnapshot:
    """
    Version snapshot value object.

    Contains metadata about the snapshot stored in R2.
    """

    id: str
    version_id: str
    r2_key: str
    created_at: datetime
    size_bytes: int | None = None
    content_hash: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class VersionComparison:
    """
    Result of comparing two versions.

    Contains differences between two study versions.
    """

    from_version: int
    to_version: int
    changes: dict[str, Any]
    additions: list[dict[str, Any]] = field(default_factory=list)
    deletions: list[dict[str, Any]] = field(default_factory=list)
    modifications: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class SnapshotContent:
    """
    Content of a version snapshot.

    Full study state at a specific version.
    """

    version_number: int
    study_id: str
    study_data: dict[str, Any]
    chapters: list[dict[str, Any]] = field(default_factory=list)
    variations: list[dict[str, Any]] = field(default_factory=list)
    annotations: list[dict[str, Any]] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "version_number": self.version_number,
            "study_id": self.study_id,
            "study_data": self.study_data,
            "chapters": self.chapters,
            "variations": self.variations,
            "annotations": self.annotations,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SnapshotContent":
        """Create from dictionary."""
        return cls(
            version_number=data["version_number"],
            study_id=data["study_id"],
            study_data=data["study_data"],
            chapters=data.get("chapters", []),
            variations=data.get("variations", []),
            annotations=data.get("annotations", []),
            timestamp=datetime.fromisoformat(data["timestamp"]),
        )


@dataclass
class CreateVersionCommand:
    """Command to create a new version."""

    study_id: str
    created_by: str
    change_summary: str | None = None
    is_rollback: bool = False


@dataclass
class RollbackCommand:
    """Command to rollback to a specific version."""

    study_id: str
    target_version: int
    user_id: str
    reason: str | None = None
