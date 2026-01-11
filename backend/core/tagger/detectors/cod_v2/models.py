"""
CoD v2 data models for context and metrics.
Keep under 100 lines per file guideline.
"""
from dataclasses import dataclass, field
from typing import Any, Dict

import chess


@dataclass
class CoDMetrics:
    """
    Metrics for Control over Dynamics detection.
    All values are deltas (played vs before/best).
    """
    # Core metrics
    volatility_drop_cp: float = 0.0
    eval_drop_cp: float = 0.0
    opp_mobility_drop: float = 0.0
    self_mobility_change: float = 0.0

    # Tactical and positional
    tension_delta: float = 0.0
    structure_gain: float = 0.0
    king_safety_gain: float = 0.0
    space_gain: float = 0.0

    # Prophylaxis-specific
    preventive_score: float = 0.0
    threat_delta: float = 0.0
    plan_drop_passed: bool = False

    # Pawn control
    opp_passed_exists: bool = False
    blockade_established: bool = False
    opp_passed_push_drop: float = 0.0
    opp_line_pressure_drop: float = 0.0
    break_candidates_delta: float = 0.0

    # Simplification
    total_active_drop: int = 0
    own_active_drop: int = 0
    opp_active_drop: int = 0
    exchange_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "volatility_drop_cp": round(self.volatility_drop_cp, 2),
            "eval_drop_cp": round(self.eval_drop_cp, 2),
            "opp_mobility_drop": round(self.opp_mobility_drop, 3),
            "preventive_score": round(self.preventive_score, 3),
        }


@dataclass
class CoDContext:
    """
    Context for CoD v2 detection.
    Focused on CoD-specific metrics and state.
    """
    board: chess.Board
    played_move: chess.Move
    actor: chess.Color
    metrics: CoDMetrics

    # Tactical context
    eval_drop_cp: int = 0
    played_kind: str = "quiet"

    # Cooldown tracking
    current_ply: int = 0
    last_cod_ply: int = -999

    # Phase and mode
    phase_bucket: str = "middlegame"
    allow_positional: bool = False
    has_dynamic_in_band: bool = False

    # Configuration
    control_cfg: Dict[str, Any] = field(default_factory=dict)
    strict_mode: bool = False


__all__ = ["CoDMetrics", "CoDContext"]
