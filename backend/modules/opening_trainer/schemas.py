"""Pydantic schemas for Opening Trainer APIs."""
from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class OpeningTrainerColor(str, Enum):
    white = "white"
    black = "black"


class OpeningTrainerProgressUpsertRequest(BaseModel):
    from_fen: str = Field(min_length=1)
    move_san: str = Field(min_length=1)
    color: OpeningTrainerColor
    correct: bool


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

