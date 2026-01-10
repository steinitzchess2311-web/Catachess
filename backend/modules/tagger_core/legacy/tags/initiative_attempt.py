"""
Initiative Attempt tag detector.

Detects when a player attempts to seize initiative through an expansive move
that increases mobility significantly, without excessive evaluation cost.

Conditions:
- mobility_delta > 0.3 (significant mobility gain)
- delta_eval > -0.5 pawns (not too costly)
- played_kind = "quiet" (not a capture)

Evidence:
- mobility_delta: Mobility change
- delta_eval: Evaluation cost
- played_kind: Move classification
"""
from ...models import TagContext, TagEvidence


MOBILITY_THRESHOLD = 0.3
EVAL_COST_LIMIT = -0.5


def detect(ctx: TagContext) -> TagEvidence:
    """
    Detect initiative attempt.

    Args:
        ctx: Tag detection context

    Returns:
        TagEvidence with detection result
    """
    gates_passed = []
    gates_failed = []
    evidence = {}

    mobility_delta = ctx.component_deltas.get("mobility", 0.0)
    delta_eval = ctx.delta_eval
    played_kind = ctx.played_kind

    # Store evidence
    evidence["mobility_delta"] = mobility_delta
    evidence["delta_eval"] = delta_eval
    evidence["eval_cost_cp"] = int(delta_eval * 100)
    evidence["played_kind"] = played_kind
    evidence["mobility_threshold"] = MOBILITY_THRESHOLD
    evidence["eval_cost_limit"] = EVAL_COST_LIMIT
    evidence["phase"] = ctx.phase_bucket

    # Gate 1: Significant mobility gain
    if mobility_delta > MOBILITY_THRESHOLD:
        gates_passed.append("mobility_expansion")
    else:
        gates_failed.append("mobility_expansion")

    # Gate 2: Acceptable eval cost
    if delta_eval > EVAL_COST_LIMIT:
        gates_passed.append("acceptable_cost")
    else:
        gates_failed.append("acceptable_cost")

    # Gate 3: Not a capture (expansion/quiet move)
    if played_kind == "quiet":
        gates_passed.append("quiet_expansion")
    else:
        gates_failed.append("quiet_expansion")

    # Fire if all gates pass
    fired = len(gates_passed) == 3

    # Compute confidence
    if fired:
        # Higher confidence for larger mobility gains and lower cost
        mobility_bonus = min(0.4, (mobility_delta - MOBILITY_THRESHOLD) * 0.5)
        cost_bonus = min(0.3, (delta_eval - EVAL_COST_LIMIT) * 0.4)
        confidence = 0.5 + mobility_bonus + cost_bonus
    else:
        confidence = 0.0

    return TagEvidence(
        tag="initiative_attempt",
        fired=fired,
        confidence=min(1.0, confidence),
        evidence=evidence,
        gates_passed=gates_passed,
        gates_failed=gates_failed,
    )


__all__ = ["detect"]
