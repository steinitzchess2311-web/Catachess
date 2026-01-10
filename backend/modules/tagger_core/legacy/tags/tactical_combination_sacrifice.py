"""
Tactical Combination Sacrifice tag detector.

Detects tactical sacrifices that are part of a forcing combination - material
sacrificed as part of a tactical sequence with clear calculation.

Conditions:
- Move is a tactical sacrifice (sound king attack)
- Strong combination signal:
  - Tactics component gains significantly (≥ 0.2), OR
  - Tactical weight is high (≥ 0.6)

This is a subtype of tactical_sacrifice that emphasizes the forcing,
calculated nature of the sacrifice.

Evidence:
- is_tactical_sacrifice: Whether tactical_sacrifice fires
- tactics_gain: Tactics component delta
- tactical_weight: Overall tactical complexity
- combination_signal: Whether combination criteria met
"""
from ...models import TagContext, TagEvidence
from . import tactical_sacrifice


# Thresholds
TACTICS_GAIN_THRESHOLD = 0.2
TACTICAL_WEIGHT_THRESHOLD = 0.6


def detect(ctx: TagContext) -> TagEvidence:
    """
    Detect tactical combination sacrifice.

    Args:
        ctx: Tag detection context

    Returns:
        TagEvidence with detection result
    """
    gates_passed = []
    gates_failed = []
    evidence = {}

    # Check if tactical_sacrifice fires
    tactical_sac_evidence = tactical_sacrifice.detect(ctx)
    is_tactical_sac = tactical_sac_evidence.fired

    evidence["is_tactical_sacrifice"] = is_tactical_sac

    # Gate 1: Must be tactical sacrifice
    if is_tactical_sac:
        gates_passed.append("is_tactical_sacrifice")
    else:
        gates_failed.append("is_tactical_sacrifice")
        return TagEvidence(
            tag="tactical_combination_sacrifice",
            fired=False,
            confidence=0.0,
            evidence=evidence,
            gates_passed=gates_passed,
            gates_failed=gates_failed,
        )

    # Check combination signals
    tactics_gain = ctx.component_deltas.get("tactics", 0.0)
    tactical_weight = ctx.tactical_weight

    evidence["tactics_gain"] = tactics_gain
    evidence["tactical_weight"] = tactical_weight

    # Gate 2: Combination signal
    combination_signal = (
        tactics_gain >= TACTICS_GAIN_THRESHOLD
        or tactical_weight >= TACTICAL_WEIGHT_THRESHOLD
    )
    evidence["combination_signal"] = combination_signal

    if combination_signal:
        gates_passed.append("combination_signal")
    else:
        gates_failed.append("combination_signal")

    # Fire if both gates pass
    fired = len(gates_passed) == 2

    # Compute confidence
    if fired:
        # Higher confidence for stronger combination signals
        base = tactical_sac_evidence.confidence * 0.7
        tactics_bonus = min(0.2, max(0.0, tactics_gain - TACTICS_GAIN_THRESHOLD) * 0.5)
        weight_bonus = min(0.1, max(0.0, tactical_weight - TACTICAL_WEIGHT_THRESHOLD) * 0.3)
        confidence = base + tactics_bonus + weight_bonus
    else:
        confidence = 0.0

    return TagEvidence(
        tag="tactical_combination_sacrifice",
        fired=fired,
        confidence=min(1.0, confidence),
        evidence=evidence,
        gates_passed=gates_passed,
        gates_failed=gates_failed,
    )


__all__ = ["detect"]
