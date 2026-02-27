"""Pydantic schemas for Opening Trainer APIs."""
from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class OpeningTrainerColor(str, Enum):
    white = "white"
    black = "black"


class OpeningTrainerMode(str, Enum):
    chapter = "chapter"
    merged = "merged"


class OpeningTrainerProgressUpsertRequest(BaseModel):
    from_fen: str = Field(min_length=1, max_length=200)
    move_san: str = Field(min_length=1, max_length=20)
    color: OpeningTrainerColor
    correct: bool

    @field_validator("from_fen", "move_san")
    @classmethod
    def _strip_non_empty(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Field cannot be empty")
        return normalized


class OpeningTrainerProgressItem(BaseModel):
    from_fen: str
    move_san: str
    color: OpeningTrainerColor
    correct_count: int
    wrong_count: int
    consecutive_correct: int
    mastered: bool
    last_practiced_at: datetime | None


class OpeningTrainerProgressListResponse(BaseModel):
    items: list[OpeningTrainerProgressItem]


class OpeningTrainerEligibilityStats(BaseModel):
    total_chapters: int
    standard_start_chapters: int
    trainable_chapters: int
    max_line_ply: int
    lines_ge_5_ply: int


class OpeningTrainerEligibilityResponse(BaseModel):
    eligible: bool
    reasons: list[str]
    stats: OpeningTrainerEligibilityStats


class OpeningTrainerRequiredMove(BaseModel):
    from_fen: str
    move_san: str
    color: OpeningTrainerColor
    move_number: int
    ply: int


class OpeningTrainerUnitNode(BaseModel):
    id: str
    kind: str
    title: str
    edge_label: str | None = None
    chapter_id: str | None = None
    line_count: int
    max_ply: int
    required_move_count: int
    required_fens: list[str] = Field(default_factory=list)
    required_moves: list[OpeningTrainerRequiredMove] = Field(default_factory=list)
    children: list["OpeningTrainerUnitNode"] = Field(default_factory=list)


class OpeningTrainerLeafUnit(BaseModel):
    id: str
    title: str
    chapter_id: str | None = None
    line_count: int
    max_ply: int
    required_move_count: int
    required_fens: list[str]
    required_moves: list[OpeningTrainerRequiredMove]
    path: list[str]


class OpeningTrainerUnitsResponse(BaseModel):
    study_id: str
    mode: OpeningTrainerMode
    color: OpeningTrainerColor
    eligibility: OpeningTrainerEligibilityResponse
    roots: list[OpeningTrainerUnitNode]
    leaf_units: list[OpeningTrainerLeafUnit]
    total_units: int


OpeningTrainerUnitNode.model_rebuild()
