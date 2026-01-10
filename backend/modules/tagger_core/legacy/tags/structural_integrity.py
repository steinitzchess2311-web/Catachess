"""
Structural Integrity tag detector.

Detects when a player improves their pawn structure significantly while
maintaining tactical opportunities.

Conditions:
- structure_delta >= 0.25 (significant structure improvement)
- tactics_delta <= 0.1 (tactics not deteriorating much)

Evidence:
- structure_delta: Change in structure metric
- tactics_delta: Change in tactics metric
- thresholds: The thresholds used for detection
"""
from ...models import TagContext, TagEvidence


STRUCTURE_GAIN_THRESHOLD = 0.25
TACTICS_LIMIT = 0.1


def detect(ctx: TagContext) -> TagEvidence:
    """
    Detect structural integrity.

    Args:
        ctx: Tag detection context

    Returns:
        TagEvidence with detection result
    """
    gates_passed = []
    gates_failed = []
    evidence = {}

    structure_gain = ctx.component_deltas.get("structure", 0.0)
    tactics_gain = ctx.component_deltas.get("tactics", 0.0)

    # Store evidence
    evidence["structure_delta"] = structure_gain
    evidence["tactics_delta"] = tactics_gain
    evidence["structure_threshold"] = STRUCTURE_GAIN_THRESHOLD
    evidence["tactics_limit"] = TACTICS_LIMIT
    evidence["phase"] = ctx.phase_bucket

    # Gate 1: Significant structure improvement
    if structure_gain >= STRUCTURE_GAIN_THRESHOLD:
        gates_passed.append("structure_improvement")
    else:
        gates_failed.append("structure_improvement")

    # Gate 2: Tactics not deteriorating much
    if tactics_gain <= TACTICS_LIMIT:
        gates_passed.append("tactics_maintained")
    else:
        gates_failed.append("tactics_maintained")

    # Fire if both gates pass
    fired = len(gates_passed) == 2

    # Compute confidence
    if fired:
        # Higher confidence for better structure gain and less tactics loss
        structure_bonus = min(0.4, (structure_gain - STRUCTURE_GAIN_THRESHOLD) * 0.8)
        tactics_bonus = 0.3 if tactics_gain >= 0 else 0.3 * (1 - abs(tactics_gain) / TACTICS_LIMIT)
        confidence = 0.5 + structure_bonus + tactics_bonus
    else:
        confidence = 0.0

    return TagEvidence(
        tag="structural_integrity",
        fired=fired,
        confidence=min(1.0, confidence),
        evidence=evidence,
        gates_passed=gates_passed,
        gates_failed=gates_failed,
    )


__all__ = ["detect"]
