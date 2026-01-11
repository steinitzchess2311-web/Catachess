"""
Study domain model.

A Study is a special type of Node that contains chapters (games).
"""

from dataclasses import dataclass
from datetime import datetime

from workspace.domain.models.types import NodeType, Visibility


@dataclass
class StudyModel:
    """
    Study domain model.

    Represents a study with metadata and chapter management.
    """

    id: str
    title: str
    owner_id: str
    description: str | None
    visibility: Visibility
    chapter_count: int
    is_public: bool
    tags: str | None
    parent_id: str | None
    path: str
    depth: int
    version: int
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None

    @property
    def is_deleted(self) -> bool:
        """Check if study is soft-deleted."""
        return self.deleted_at is not None

    @property
    def is_full(self) -> bool:
        """Check if study has reached 64-chapter limit."""
        return self.chapter_count >= 64

    @property
    def available_slots(self) -> int:
        """Get number of available chapter slots."""
        return max(0, 64 - self.chapter_count)


@dataclass
class CreateStudyCommand:
    """
    Command to create a new study.

    Args:
        title: Study title
        owner_id: Owner user ID
        parent_id: Parent node (workspace or folder)
        description: Optional description
        visibility: Visibility setting
        tags: Optional tags (comma-separated)
    """

    title: str
    owner_id: str
    parent_id: str | None = None
    description: str | None = None
    visibility: Visibility = Visibility.PRIVATE
    tags: str | None = None


@dataclass
class UpdateStudyCommand:
    """
    Command to update study metadata.

    Args:
        study_id: Study ID
        title: Optional new title
        description: Optional new description
        visibility: Optional new visibility
        tags: Optional new tags
        version: Expected version for optimistic locking
    """

    study_id: str
    version: int
    title: str | None = None
    description: str | None = None
    visibility: Visibility | None = None
    tags: str | None = None


@dataclass
class ImportPGNCommand:
    """
    Command to import PGN content into a study.

    Args:
        parent_id: Parent node (workspace or folder) for new studies
        owner_id: Owner of the imported studies
        pgn_content: Raw PGN content
        base_title: Base title for the study/studies
        auto_split: Whether to auto-split if > 64 chapters
        visibility: Visibility for imported studies
    """

    parent_id: str
    owner_id: str
    pgn_content: str
    base_title: str
    auto_split: bool = True
    visibility: Visibility = Visibility.PRIVATE


@dataclass
class ImportResult:
    """
    Result of PGN import operation.

    Attributes:
        total_chapters: Total chapters imported
        studies_created: List of created study IDs
        folder_id: If split occurred, the folder containing studies
        was_split: Whether PGN was split into multiple studies
    """

    total_chapters: int
    studies_created: list[str]
    folder_id: str | None
    was_split: bool

    @property
    def single_study(self) -> bool:
        """Check if import created single study."""
        return len(self.studies_created) == 1 and not self.was_split
