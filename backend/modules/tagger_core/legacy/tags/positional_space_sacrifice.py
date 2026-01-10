"""
Positional Space Sacrifice tag detector.

Detects positional sacrifices made for space and activity advantages -
material sacrificed to gain mobility, central control, or piece activity.

Conditions:
- Move is a positional sacrifice (sound non-tactical sacrifice)
- Strong space signal:
  - Mobility gains significantly (≥ 0.1), OR
  - Center control gains significantly (≥ 0.1), OR
  - No structure signal (default positional type)

This is a subtype of positional_sacrifice that emphasizes dynamic
factors like activity and space over static structural factors.

Evidence:
- is_positional_sacrifice: Whether positional_sacrifice fires
- mobility_gain: Mobility component delta
- center_gain: Center control delta
- space_signal: Whether space criteria met
"""
from ...models import TagContext, TagEvidence
from . import positional_sacrifice


# Thresholds
MOBILITY_GAIN_THRESHOLD = 0.1
CENTER_GAIN_THRESHOLD = 0.1
STRUCTURE_GAIN_THRESHOLD = 0.15
KING_GAIN_THRESHOLD = 0.1


def detect(ctx: TagContext) -> TagEvidence:
    """
    Detect positional space sacrifice.

    Args:
        ctx: Tag detection context

    Returns:
        TagEvidence with detection result
    """
    gates_passed = []
    gates_failed = []
    evidence = {}

    # Check if positional_sacrifice fires
    positional_sac_evidence = positional_sacrifice.detect(ctx)
    is_positional_sac = positional_sac_evidence.fired

    evidence["is_positional_sacrifice"] = is_positional_sac

    # Gate 1: Must be positional sacrifice
    if is_positional_sac:
        gates_passed.append("is_positional_sacrifice")
    else:
        gates_failed.append("is_positional_sacrifice")
        return TagEvidence(
            tag="positional_space_sacrifice",
            fired=False,
            confidence=0.0,
            evidence=evidence,
            gates_passed=gates_passed,
            gates_failed=gates_failed,
        )

    # Check space signals
    mobility_gain = ctx.component_deltas.get("mobility", 0.0)
    center_gain = ctx.component_deltas.get("center_control", 0.0)

    # Also check structure to determine if this is space-based or default
    structure_gain = ctx.component_deltas.get("structure", 0.0)
    king_gain = ctx.component_deltas.get("king_safety", 0.0)
    structure_signal = (
        structure_gain >= STRUCTURE_GAIN_THRESHOLD
        or king_gain >= KING_GAIN_THRESHOLD
    )

    evidence["mobility_gain"] = mobility_gain
    evidence["center_gain"] = center_gain
    evidence["structure_signal"] = structure_signal

    # Gate 2: Space signal OR no structure signal (default)
    space_signal = (
        mobility_gain >= MOBILITY_GAIN_THRESHOLD
        or center_gain >= CENTER_GAIN_THRESHOLD
        or not structure_signal
    )
    evidence["space_signal"] = space_signal

    if space_signal:
        gates_passed.append("space_signal")
    else:
        gates_failed.append("space_signal")

    # Fire if both gates pass
    fired = len(gates_passed) == 2

    # Compute confidence
    if fired:
        # Higher confidence for stronger space gains
        base = positional_sac_evidence.confidence * 0.7
        mobility_bonus = min(0.15, max(0.0, mobility_gain - MOBILITY_GAIN_THRESHOLD) * 0.8)
        center_bonus = min(0.15, max(0.0, center_gain - CENTER_GAIN_THRESHOLD) * 0.8)
        confidence = base + mobility_bonus + center_bonus
    else:
        confidence = 0.0

    return TagEvidence(
        tag="positional_space_sacrifice",
        fired=fired,
        confidence=min(1.0, confidence),
        evidence=evidence,
        gates_passed=gates_passed,
        gates_failed=gates_failed,
    )


__all__ = ["detect"]
