"""
Preventive score computation and soft weight calculation.

Based on catachess implementation with rule_tagger2 alignment.
"""
from typing import Dict, Any

from .config import ProphylaxisConfig, OPENING_MOVE_CUTOFF
# Note: TagContext import removed to avoid circular dependencies
# Functions accept component_deltas dicts directly


def compute_preventive_score_from_deltas(
    opp_mobility_delta: float,
    opp_tactics_delta: float,
) -> Dict[str, Any]:
    """
    Compute preventive score based on opponent restriction.

    Args:
        opp_mobility_delta: Opponent mobility change
        opp_tactics_delta: Opponent tactics change

    Returns:
        Dict with preventive_score and component breakdowns
    """
    # Compute opponent trend (simplified: just mobility + tactics)
    opp_trend = opp_mobility_delta + opp_tactics_delta

    # Preventive score: reward opponent restriction
    preventive_score = (
        max(0.0, -opp_mobility_delta) * 0.3
        + max(0.0, -opp_tactics_delta) * 0.2
        + max(0.0, -opp_trend) * 0.15
    )

    return {
        "preventive_score": round(preventive_score, 3),
        "opp_mobility_delta": round(opp_mobility_delta, 3),
        "opp_tactics_delta": round(opp_tactics_delta, 3),
        "opp_trend": round(opp_trend, 3),
        "opp_restrained": (
            opp_trend < 0.0
            or opp_mobility_delta <= -0.05
            or opp_tactics_delta <= -0.1
        ),
    }


def compute_soft_weight_from_deltas(
    structure_delta: float,
    king_safety_delta: float,
    mobility_delta: float,
    safety_cap: float = 0.6,
) -> float:
    """
    Compute soft positioning weight based on self-consolidation.

    Args:
        structure_delta: Structure change
        king_safety_delta: King safety change
        mobility_delta: Mobility change
        safety_cap: Maximum score cap

    Returns:
        Soft weight score (0.0 to safety_cap)
    """
    soft_raw = (
        max(0.0, structure_delta) * 0.4
        + max(0.0, king_safety_delta) * 0.4
        + max(0.0, -mobility_delta) * 0.2
    )

    return round(min(soft_raw, safety_cap), 3)


def clamp_preventive_score(score: float, *, config: ProphylaxisConfig) -> float:
    """
    Limit the preventive score to a sensible range for downstream thresholds.

    Matches rule_tagger2/legacy/prophylaxis.py:242-246 exactly.

    Args:
        score: Raw preventive score
        config: Prophylaxis configuration

    Returns:
        Clamped score (0.0 to config.safety_cap)
    """
    if score <= 0.0:
        return 0.0
    return min(score, config.safety_cap)
