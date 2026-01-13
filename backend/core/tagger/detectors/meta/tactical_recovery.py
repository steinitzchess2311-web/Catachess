"""
Tactical Recovery tag detector.

Detects when a player recovers from a near-losing position through a
tactical move that significantly improves the evaluation.

Conditions:
- eval_before <= -3.0 pawns (near loss)
- eval_played >= -1.0 pawns (recovered to manageable position)

Evidence:
- eval_before: Evaluation before the move
- eval_played: Evaluation after the move
- recovery_amount: How much evaluation improved
"""
from ...models import TagContext, TagEvidence


def detect(ctx: TagContext) -> TagEvidence:
    """
    Detect tactical recovery.

    Args:
        ctx: Tag detection context

    Returns:
        TagEvidence with detection result
    """
    gates_passed = []
    gates_failed = []
    evidence = {}

    # Thresholds
    losing_threshold = -3.0  # -3 pawns (near loss)
    recovery_target = -1.0   # -1 pawn (recovered position)

    eval_before = ctx.eval_before
    eval_played = ctx.eval_played
    recovery_amount = eval_played - eval_before

    # Store evidence
    evidence["eval_before"] = eval_before
    evidence["eval_played"] = eval_played
    evidence["recovery_amount"] = recovery_amount
    evidence["losing_threshold"] = losing_threshold
    evidence["recovery_target"] = recovery_target
    evidence["tactical_weight"] = ctx.tactical_weight

    # Gate 1: Was in losing position
    if eval_before <= losing_threshold:
        gates_passed.append("losing_position")
    else:
        gates_failed.append("losing_position")

    # Gate 2: Recovered to manageable position
    if eval_played >= recovery_target:
        gates_passed.append("recovered_position")
    else:
        gates_failed.append("recovered_position")

    # Fire if both gates pass
    fired = len(gates_passed) == 2

    # Compute confidence
    if fired:
        # Higher confidence for larger recoveries
        depth_of_loss = abs(eval_before - losing_threshold)
        recovery_quality = eval_played - recovery_target
        confidence = 0.5 + min(0.3, depth_of_loss * 0.1) + min(0.2, recovery_quality * 0.15)
    else:
        confidence = 0.0

    return TagEvidence(
        tag="tactical_recovery",
        fired=fired,
        confidence=min(1.0, confidence),
        evidence=evidence,
        gates_passed=gates_passed,
        gates_failed=gates_failed,
    )


__all__ = ["detect"]
