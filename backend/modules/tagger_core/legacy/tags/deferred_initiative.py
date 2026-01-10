"""
Deferred Initiative tag detector.

Detects when a player makes a quiet, consolidating move that maintains
stability while deferring immediate initiative/activity. This is often
seen in positional play or prophylactic moves.

Conditions:
- played_kind = "quiet" (not forcing)
- delta_eval > -0.5 pawns (maintains position)
- mobility_delta < 0.2 (not expanding activity much)
- contact_ratio_played < contact_ratio_before + 0.1 (not creating tension)

Evidence:
- delta_eval: Evaluation change
- mobility_delta: Mobility change
- contact_ratio_delta: Change in contact ratio
- played_kind: Move classification
"""
from ...models import TagContext, TagEvidence


EVAL_THRESHOLD = -0.5
MOBILITY_LIMIT = 0.2
CONTACT_INCREASE_LIMIT = 0.1


def detect(ctx: TagContext) -> TagEvidence:
    """
    Detect deferred initiative.

    Args:
        ctx: Tag detection context

    Returns:
        TagEvidence with detection result
    """
    gates_passed = []
    gates_failed = []
    evidence = {}

    delta_eval = ctx.delta_eval
    mobility_delta = ctx.component_deltas.get("mobility", 0.0)
    played_kind = ctx.played_kind
    contact_delta = ctx.contact_ratio_played - ctx.contact_ratio_before

    # Store evidence
    evidence["delta_eval"] = delta_eval
    evidence["mobility_delta"] = mobility_delta
    evidence["contact_delta"] = contact_delta
    evidence["played_kind"] = played_kind
    evidence["eval_threshold"] = EVAL_THRESHOLD
    evidence["mobility_limit"] = MOBILITY_LIMIT
    evidence["phase"] = ctx.phase_bucket

    # Gate 1: Quiet move
    if played_kind == "quiet":
        gates_passed.append("quiet_move")
    else:
        gates_failed.append("quiet_move")

    # Gate 2: Maintains position (eval not too negative)
    if delta_eval > EVAL_THRESHOLD:
        gates_passed.append("maintains_stability")
    else:
        gates_failed.append("maintains_stability")

    # Gate 3: Limited mobility increase (not expanding)
    if mobility_delta < MOBILITY_LIMIT:
        gates_passed.append("limited_activity")
    else:
        gates_failed.append("limited_activity")

    # Gate 4: Not creating tension
    if contact_delta < CONTACT_INCREASE_LIMIT:
        gates_passed.append("low_tension_creation")
    else:
        gates_failed.append("low_tension_creation")

    # Fire if all gates pass
    fired = len(gates_passed) == 4

    # Compute confidence
    if fired:
        # Higher confidence for more conservative moves
        stability_bonus = min(0.3, (delta_eval - EVAL_THRESHOLD) * 0.4)
        quietness_bonus = 0.3 if mobility_delta <= 0 else 0.3 * (1 - mobility_delta / MOBILITY_LIMIT)
        confidence = 0.5 + stability_bonus + quietness_bonus
    else:
        confidence = 0.0

    return TagEvidence(
        tag="deferred_initiative",
        fired=fired,
        confidence=min(1.0, confidence),
        evidence=evidence,
        gates_passed=gates_passed,
        gates_failed=gates_failed,
    )


__all__ = ["detect"]
