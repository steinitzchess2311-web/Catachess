"""
TagResult - Complete tagging result matching legacy schema.
Split from models.py to maintain ≤150 line file limit.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class TagResult:
    """
    Complete tagging result matching the legacy TagResult schema.
    This is the final output of the tagging pipeline.
    """
    # Move info
    played_move: str
    played_kind: str
    best_move: str
    best_kind: str

    # Evaluations
    eval_before: float
    eval_played: float
    eval_best: float
    delta_eval: float

    # Control over Dynamics tags (parent + 9 subtypes)
    control_over_dynamics: bool = False
    control_over_dynamics_subtype: Optional[str] = None
    cod_simplify: bool = False
    cod_plan_kill: bool = False
    cod_freeze_bind: bool = False
    cod_blockade_passed: bool = False
    cod_file_seal: bool = False
    cod_king_safety_shell: bool = False
    cod_space_clamp: bool = False
    cod_regroup_consolidate: bool = False
    cod_slowdown: bool = False

    # Semantic control tags (no gating)
    control_simplify: bool = False
    control_plan_kill: bool = False
    control_freeze_bind: bool = False
    control_blockade_passed: bool = False
    control_file_seal: bool = False
    control_king_safety_shell: bool = False
    control_space_clamp: bool = False
    control_regroup_consolidate: bool = False
    control_slowdown: bool = False
    control_schema_version: int = 1

    # Initiative tags (4)
    deferred_initiative: bool = False
    risk_avoidance: bool = False
    initiative_exploitation: bool = False
    initiative_attempt: bool = False

    # Structure tags (3)
    structural_integrity: bool = False
    structural_compromise_dynamic: bool = False
    structural_compromise_static: bool = False

    # Meta tags (7)
    tactical_sensitivity: bool = False
    first_choice: bool = False
    missed_tactic: bool = False
    conversion_precision: bool = False
    panic_move: bool = False
    tactical_recovery: bool = False

    # Tension tags (4)
    tension_creation: bool = False
    neutral_tension_creation: bool = False
    premature_attack: bool = False
    file_pressure_c: bool = False

    # Maneuver tags (5)
    constructive_maneuver: bool = False
    constructive_maneuver_prepare: bool = False
    neutral_maneuver: bool = False
    misplaced_maneuver: bool = False
    maneuver_opening: bool = False

    # Opening tags (2)
    opening_central_pawn_move: bool = False
    opening_rook_pawn_move: bool = False

    # Sacrifice tags (9)
    tactical_sacrifice: bool = False
    positional_sacrifice: bool = False
    inaccurate_tactical_sacrifice: bool = False
    speculative_sacrifice: bool = False
    desperate_sacrifice: bool = False
    tactical_combination_sacrifice: bool = False
    tactical_initiative_sacrifice: bool = False
    positional_structure_sacrifice: bool = False
    positional_space_sacrifice: bool = False

    # Prophylaxis tags (5 + score)
    prophylactic_move: bool = False
    prophylactic_direct: bool = False
    prophylactic_latent: bool = False
    prophylactic_meaningless: bool = False
    failed_prophylactic: bool = False
    prophylaxis_score: float = 0.0

    # Knight-Bishop exchange tags (3)
    accurate_knight_bishop_exchange: bool = False
    inaccurate_knight_bishop_exchange: bool = False
    bad_knight_bishop_exchange: bool = False

    # Metrics & deltas
    metrics_before: Dict[str, float] = field(default_factory=dict)
    metrics_played: Dict[str, float] = field(default_factory=dict)
    metrics_best: Dict[str, float] = field(default_factory=dict)
    component_deltas: Dict[str, float] = field(default_factory=dict)
    opp_metrics_before: Dict[str, float] = field(default_factory=dict)
    opp_metrics_played: Dict[str, float] = field(default_factory=dict)
    opp_metrics_best: Dict[str, float] = field(default_factory=dict)
    opp_component_deltas: Dict[str, float] = field(default_factory=dict)

    # Context and scoring
    coverage_delta: int = 0
    tactical_weight: float = 0.0
    mode: str = "neutral"
    analysis_context: Dict[str, Any] = field(default_factory=dict)
    notes: Dict[str, str] = field(default_factory=dict)

    # Maneuver scoring
    maneuver_precision_score: float = 0.0
    maneuver_timing_score: float = 0.0
    prepare_quality_score: float = 0.0
    prepare_consensus_score: float = 0.0


__all__ = ["TagResult"]
