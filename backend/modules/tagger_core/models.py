"""
Core data models for tag detection context and evidence.
Following Phase B: Data Contract White-Boxing.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

import chess


@dataclass
class Candidate:
    """A candidate move from engine analysis."""
    move: chess.Move
    score_cp: int
    kind: str  # "quiet", "dynamic", or "forcing"


@dataclass
class TagEvidence:
    """
    Evidence bundle for a single tag detection.

    This is the output from each independent tag detector,
    containing the tag name, whether it fired, and the reasoning.
    """
    tag: str
    fired: bool
    confidence: float  # 0.0 to 1.0
    evidence: Dict[str, Any]  # Serializable evidence (thresholds, metrics, reasons)
    gates_passed: List[str]  # Which gating conditions passed
    gates_failed: List[str]  # Which gating conditions failed


@dataclass
class TagContext:
    """
    Unified read-only context for tag detection.

    All tag detectors receive this context and must not modify it.
    Following the plan's requirement for explicit context passing.
    """
    # Board state
    board: chess.Board
    fen: str
    played_move: chess.Move
    actor: chess.Color

    # Engine analysis
    candidates: List[Candidate]
    best_move: chess.Move
    played_kind: str
    best_kind: str

    # Evaluations (centipawns)
    eval_before_cp: int
    eval_played_cp: int
    eval_best_cp: int

    # Evaluations (normalized float)
    eval_before: float
    eval_played: float
    eval_best: float
    delta_eval: float

    # Metrics (5 dimensions per position)
    metrics_before: Dict[str, float]
    metrics_played: Dict[str, float]
    metrics_best: Dict[str, float]
    component_deltas: Dict[str, float]

    # Opponent metrics
    opp_metrics_before: Dict[str, float]
    opp_metrics_played: Dict[str, float]
    opp_metrics_best: Dict[str, float]
    opp_component_deltas: Dict[str, float]

    # Game phase
    phase_ratio: float  # 0.0 = opening, 1.0 = endgame
    phase_bucket: str  # "opening", "middlegame", "endgame"

    # Contact metrics (capture/check ratio)
    contact_ratio_before: float
    contact_ratio_played: float
    contact_ratio_best: float

    # Computed features
    tactical_weight: float
    coverage_delta: int

    # Additional analysis metadata
    has_dynamic_in_band: bool
    analysis_meta: Dict[str, Any]  # Shared state for legacy compatibility

    # Engine parameters
    engine_depth: int
    engine_multipv: int


__all__ = [
    "Candidate",
    "TagContext",
    "TagEvidence",
]
