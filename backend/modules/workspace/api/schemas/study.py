"""
Study API schemas.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from modules.workspace.domain.models.types import Visibility


class StudyCreate(BaseModel):
    """Schema for creating a study."""

    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=5000)
    parent_id: str | None = None
    visibility: Visibility = Visibility.PRIVATE
    tags: str | None = Field(None, max_length=500)


class StudyUpdate(BaseModel):
    """Schema for updating a study."""

    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=5000)
    visibility: Visibility | None = None
    tags: str | None = Field(None, max_length=500)
    version: int


class StudyImportPGN(BaseModel):
    """Schema for importing PGN."""

    pgn_content: str = Field(..., min_length=1)
    base_title: str = Field(..., min_length=1, max_length=200)
    parent_id: str | None = None
    auto_split: bool = True
    visibility: Visibility = Visibility.PRIVATE


class ChapterCreate(BaseModel):
    """Schema for creating a chapter."""

    title: str = Field(..., min_length=1, max_length=200)


class ChapterImportPGN(BaseModel):
    """Schema for importing PGN into an existing study."""

    pgn_content: str = Field(..., min_length=1)


class ChapterResponse(BaseModel):
    """Schema for chapter response."""

    model_config = ConfigDict(from_attributes=True)

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
    pgn_status: str | None
    r2_etag: str | None
    last_synced_at: datetime | None
    created_at: datetime
    updated_at: datetime


class StudyResponse(BaseModel):
    """Schema for study response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    description: str | None
    owner_id: str
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
    deleted_at: datetime | None


class StudyWithChaptersResponse(BaseModel):
    """Schema for study with chapters."""

    study: StudyResponse
    chapters: list[ChapterResponse]


class ImportResultResponse(BaseModel):
    """Schema for import result."""

    total_chapters: int
    studies_created: list[str]
    folder_id: str | None
    was_split: bool
    single_study: bool


class ChapterPgnResponse(BaseModel):
    """Schema for chapter PGN response."""

    pgn_text: str
    pgn_hash: str | None
    pgn_size: int | None
    last_synced_at: datetime | None
