"""
Chapter domain model.

A Chapter represents a single game (PGN) within a Study.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class ChapterModel:
    """
    Chapter domain model.

    Each chapter stores one game's PGN content in R2.
    """

    id: str
    study_id: str
    title: str
    order: int
    white: str | None
    black: str | None
    event: str | None
    date: str | None
    result: str | None
    r2_key: str
    pgn_hash: str | None
    pgn_size: int | None
    r2_etag: str | None
    last_synced_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @property
    def has_integrity_info(self) -> bool:
        """Check if chapter has integrity information."""
        return self.pgn_hash is not None and self.pgn_size is not None

    @property
    def is_synced(self) -> bool:
        """Check if chapter is synced with R2."""
        return self.r2_etag is not None and self.last_synced_at is not None


@dataclass
class AddChapterCommand:
    """
    Command to add a chapter to a study.

    Args:
        study_id: Study ID
        title: Chapter title
        pgn_content: PGN content for this chapter
        order: Chapter order (0-based)
        white: White player name (optional, extracted from PGN)
        black: Black player name (optional, extracted from PGN)
        event: Event name (optional, extracted from PGN)
        date: Game date (optional, extracted from PGN)
        result: Game result (optional, extracted from PGN)
    """

    study_id: str
    title: str
    pgn_content: str
    order: int
    white: str | None = None
    black: str | None = None
    event: str | None = None
    date: str | None = None
    result: str | None = None


@dataclass
class UpdateChapterCommand:
    """
    Command to update chapter metadata.

    Args:
        chapter_id: Chapter ID
        title: Optional new title
        order: Optional new order
    """

    chapter_id: str
    title: str | None = None
    order: int | None = None


@dataclass
class DeleteChapterCommand:
    """
    Command to delete a chapter.

    Args:
        chapter_id: Chapter ID
        delete_from_r2: Whether to delete from R2 storage
    """

    chapter_id: str
    delete_from_r2: bool = True
