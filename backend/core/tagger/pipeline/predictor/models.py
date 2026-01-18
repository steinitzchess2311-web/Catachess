from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class PlayerProfile:
    name: str
    weights: Dict[str, float]
    total_weight: float
    source_path: Optional[str] = None

    def weight_for(self, tag: str) -> float:
        return self.weights.get(tag, 0.0)


@dataclass(frozen=True)
class CandidateInfo:
    move_uci: str
    score_cp: int
    kind: str
    multipv: int
    tags: List[str]


@dataclass(frozen=True)
class MoveScore:
    move_uci: str
    similarity: float
    probability: float
    matched_weight: float
    coverage: float
    tag_count: int
    tags: List[str]
    score_cp: int
    kind: str
    multipv: int


@dataclass(frozen=True)
class ProfilePrediction:
    profile_name: str
    moves: List[MoveScore]


@dataclass(frozen=True)
class PredictionResult:
    fen: str
    profiles: List[ProfilePrediction]
