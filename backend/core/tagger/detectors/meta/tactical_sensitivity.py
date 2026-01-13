"""
Tactical Sensitivity tag detector.

Detects when a position has high tactical complexity, indicating that
accurate calculation is critical and small differences in moves can lead
to large evaluation swings.

Condition:
- tactical_weight > TACTICAL_THRESHOLD (typically 0.15)

Evidence:
- tactical_weight: The computed tactical weight (0.0-1.0)
- threshold: The threshold that was exceeded
- contact_ratio: Proportion of forcing moves
- delta_tactics: Change in tactical metric
"""
from ...models import TagContext, TagEvidence
from ...config import TACTICAL_THRESHOLD


def detect(ctx: TagContext) -> TagEvidence:
    """
    Detect tactical sensitivity.

    Args:
        ctx: Tag detection context

    Returns:
        TagEvidence with detection result
    """
    gates_passed = []
    gates_failed = []
    evidence = {}

    threshold = TACTICAL_THRESHOLD
    tac_weight = ctx.tactical_weight
    contact_ratio = ctx.contact_ratio_before
    delta_tactics = ctx.component_deltas.get("tactics", 0.0)

    # Store evidence values
    evidence["tactical_weight"] = tac_weight
    evidence["threshold"] = threshold
    evidence["contact_ratio"] = contact_ratio
    evidence["delta_tactics"] = delta_tactics
    evidence["phase"] = ctx.phase_bucket

    # Gate: High tactical weight
    if tac_weight > threshold:
        gates_passed.append("high_tactical_weight")
        fired = True
    else:
        gates_failed.append("high_tactical_weight")
        fired = False

    # Compute confidence based on how much tactical weight exceeds threshold
    if fired:
        excess = tac_weight - threshold
        confidence = min(1.0, 0.5 + excess * 2.0)
    else:
        confidence = 0.0

    return TagEvidence(
        tag="tactical_sensitivity",
        fired=fired,
        confidence=confidence,
        evidence=evidence,
        gates_passed=gates_passed,
        gates_failed=gates_failed,
    )


__all__ = ["detect"]
