"""
Gate checking logic for CoD v2.
Each gate must pass before subtype detection.
"""
from typing import Tuple, List

from .models import CoDContext
from .thresholds import CoDThresholds


def check_tactical_weight_gate(
    ctx: CoDContext,
    thresholds: CoDThresholds,
) -> Tuple[bool, str]:
    """
    Check if tactical weight is below ceiling.

    Args:
        ctx: CoD context
        thresholds: Threshold configuration

    Returns:
        (passed, reason)
    """
    # TODO: Get tactical_weight from context
    # For now assume it's in control_cfg
    tactical_weight = ctx.control_cfg.get("tactical_weight", 0.0)

    if tactical_weight > thresholds.tactical_weight_ceiling:
        return False, f"tactical_weight {tactical_weight:.2f} > {thresholds.tactical_weight_ceiling}"

    return True, "tactical_weight_ok"


def check_mate_threat_gate(
    ctx: CoDContext,
    thresholds: CoDThresholds,
) -> Tuple[bool, str]:
    """Check if mate threat gate passes."""
    if not thresholds.mate_threat_gate:
        return True, "mate_gate_disabled"

    mate_threat = ctx.control_cfg.get("mate_threat", False)
    if mate_threat:
        return False, "mate_threat_present"

    return True, "no_mate_threat"


def check_blunder_gate(
    ctx: CoDContext,
    thresholds: CoDThresholds,
) -> Tuple[bool, str]:
    """Check if eval drop indicates blunder."""
    if abs(ctx.eval_drop_cp) > thresholds.blunder_threat_thresh * 100:
        return False, f"blunder_eval_drop_{ctx.eval_drop_cp}cp"

    return True, "not_blunder"


def check_all_gates(
    ctx: CoDContext,
    thresholds: CoDThresholds,
) -> Tuple[bool, List[str]]:
    """
    Check all gates.

    Returns:
        (all_passed, failed_gates)
    """
    failed = []

    passed, reason = check_tactical_weight_gate(ctx, thresholds)
    if not passed:
        failed.append(reason)

    passed, reason = check_mate_threat_gate(ctx, thresholds)
    if not passed:
        failed.append(reason)

    passed, reason = check_blunder_gate(ctx, thresholds)
    if not passed:
        failed.append(reason)

    return len(failed) == 0, failed


__all__ = ["check_all_gates"]
