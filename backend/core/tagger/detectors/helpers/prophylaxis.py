"""
Prophylaxis detection helpers (re-export from split modules).

This module maintains backward compatibility by re-exporting all functions
from the split prophylaxis_modules/ directory. Each submodule is < 100 lines.

Original monolithic file was 451 lines. Now split into:
- config.py (38 lines): Configuration dataclass
- candidate.py (68 lines): Candidate filtering
- threat.py (76 lines): Threat estimation
- pattern.py (42 lines): Pattern detection
- score.py (92 lines): Score computation
- classify.py (110 lines): Classification logic

All functions match rule_tagger2/legacy/prophylaxis.py exactly.
"""
from .prophylaxis_modules import (
    # Config
    ProphylaxisConfig,
    FULL_MATERIAL_COUNT,
    OPENING_MOVE_CUTOFF,
    # Candidate filtering
    is_prophylaxis_candidate,
    is_full_material,
    # Threat estimation
    estimate_opponent_threat,
    # Pattern detection
    prophylaxis_pattern_reason,
    # Score computation
    compute_preventive_score_from_deltas,
    compute_soft_weight_from_deltas,
    clamp_preventive_score,
    # Classification
    classify_prophylaxis_quality,
)

# Legacy imports for backward compatibility (ctx-based versions)
from typing import Dict, Any
try:
    from backend.core.tagger.models import TagContext

    def compute_preventive_score(ctx: TagContext) -> Dict[str, Any]:
        """
        Compute preventive score from TagContext (backward compatible).

        This wraps the new compute_preventive_score_from_deltas function.
        """
        return compute_preventive_score_from_deltas(
            opp_mobility_delta=ctx.opp_component_deltas.get("mobility", 0.0),
            opp_tactics_delta=ctx.opp_component_deltas.get("tactics", 0.0),
        )

    def compute_soft_weight(ctx: TagContext) -> float:
        """
        Compute soft weight from TagContext (backward compatible).

        This wraps the new compute_soft_weight_from_deltas function.
        """
        return compute_soft_weight_from_deltas(
            structure_delta=ctx.component_deltas.get("structure", 0.0),
            king_safety_delta=ctx.component_deltas.get("king_safety", 0.0),
            mobility_delta=ctx.component_deltas.get("mobility", 0.0),
        )

except ImportError:
    # If TagContext not available (e.g., in tests), skip wrapper functions
    pass


# Legacy threshold constants (for backward compatibility)
STRUCTURE_MIN = 0.2
OPP_MOBILITY_DROP = 0.15
SELF_MOBILITY_TOL = 0.3
PREVENTIVE_TRIGGER = 0.16
SAFETY_CAP = 0.6
SCORE_THRESHOLD = 0.20
THREAT_DROP = 0.35


__all__ = [
    "ProphylaxisConfig",
    "FULL_MATERIAL_COUNT",
    "OPENING_MOVE_CUTOFF",
    "is_prophylaxis_candidate",
    "is_full_material",
    "estimate_opponent_threat",
    "prophylaxis_pattern_reason",
    "compute_preventive_score_from_deltas",
    "compute_soft_weight_from_deltas",
    "clamp_preventive_score",
    "classify_prophylaxis_quality",
    "compute_preventive_score",  # Backward compatible wrapper
    "compute_soft_weight",        # Backward compatible wrapper
    "STRUCTURE_MIN",
    "OPP_MOBILITY_DROP",
    "SELF_MOBILITY_TOL",
    "PREVENTIVE_TRIGGER",
    "SAFETY_CAP",
    "SCORE_THRESHOLD",
    "THREAT_DROP",
]
