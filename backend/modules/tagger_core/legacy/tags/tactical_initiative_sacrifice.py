"""
Tactical Initiative Sacrifice tag detector.

Detects tactical sacrifices aimed at seizing the initiative - material
sacrificed to gain activity, mobility, and attacking chances against the king.

Conditions:
- Move is a tactical sacrifice (sound king attack)
- Strong initiative signal:
  - Mobility gains significantly (≥ 0.1), OR
  - Center control gains significantly (≥ 0.1)

This is a subtype of tactical_sacrifice that emphasizes dynamic play
and activity over pure calculation.

Evidence:
- is_tactical_sacrifice: Whether tactical_sacrifice fires
- mobility_gain: Mobility component delta
- center_gain: Center control delta
- initiative_signal: Whether initiative criteria met
"""
from ...models import TagContext, TagEvidence
from . import tactical_sacrifice


# Thresholds
MOBILITY_GAIN_THRESHOLD = 0.1
CENTER_GAIN_THRESHOLD = 0.1


def detect(ctx: TagContext) -> TagEvidence:
    """
    Detect tactical initiative sacrifice.

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
            tag="tactical_initiative_sacrifice",
            fired=False,
            confidence=0.0,
            evidence=evidence,
            gates_passed=gates_passed,
            gates_failed=gates_failed,
        )

    # Check initiative signals
    mobility_gain = ctx.component_deltas.get("mobility", 0.0)
    center_gain = ctx.component_deltas.get("center_control", 0.0)

    evidence["mobility_gain"] = mobility_gain
    evidence["center_gain"] = center_gain

    # Gate 2: Initiative signal
    initiative_signal = (
        mobility_gain >= MOBILITY_GAIN_THRESHOLD
        or center_gain >= CENTER_GAIN_THRESHOLD
    )
    evidence["initiative_signal"] = initiative_signal

    if initiative_signal:
        gates_passed.append("initiative_signal")
    else:
        gates_failed.append("initiative_signal")

    # Fire if both gates pass
    fired = len(gates_passed) == 2

    # Compute confidence
    if fired:
        # Higher confidence for stronger initiative gains
        base = tactical_sac_evidence.confidence * 0.7
        mobility_bonus = min(0.15, max(0.0, mobility_gain - MOBILITY_GAIN_THRESHOLD) * 0.8)
        center_bonus = min(0.15, max(0.0, center_gain - CENTER_GAIN_THRESHOLD) * 0.8)
        confidence = base + mobility_bonus + center_bonus
    else:
        confidence = 0.0

    return TagEvidence(
        tag="tactical_initiative_sacrifice",
        fired=fired,
        confidence=min(1.0, confidence),
        evidence=evidence,
        gates_passed=gates_passed,
        gates_failed=gates_failed,
    )


__all__ = ["detect"]
