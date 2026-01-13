"""
Panic Move tag detector.

Detects when a player makes a move that causes a large evaluation drop
accompanied by a significant mobility loss, indicating a panicked or
poorly calculated move.

Conditions:
- delta_eval <= -2.5 pawns (large eval drop)
- mobility_delta <= -0.8 (significant mobility loss)

Evidence:
- delta_eval: Evaluation change
- mobility_delta: Change in mobility metric
- eval_drop_cp: Evaluation drop in centipawns
"""
from ...models import TagContext, TagEvidence


def detect(ctx: TagContext) -> TagEvidence:
    """
    Detect panic move.

    Args:
        ctx: Tag detection context

    Returns:
        TagEvidence with detection result
    """
    gates_passed = []
    gates_failed = []
    evidence = {}

    # Thresholds
    eval_drop_threshold = -2.5  # -2.5 pawns
    mobility_drop_threshold = -0.8  # Large mobility loss

    delta_eval = ctx.delta_eval
    mobility_delta = ctx.component_deltas.get("mobility", 0.0)

    # Store evidence
    evidence["delta_eval"] = delta_eval
    evidence["eval_drop_cp"] = int(delta_eval * 100)
    evidence["mobility_delta"] = mobility_delta
    evidence["eval_drop_threshold"] = eval_drop_threshold
    evidence["mobility_drop_threshold"] = mobility_drop_threshold

    # Gate 1: Large evaluation drop
    if delta_eval <= eval_drop_threshold:
        gates_passed.append("large_eval_drop")
    else:
        gates_failed.append("large_eval_drop")

    # Gate 2: Significant mobility loss
    if mobility_delta <= mobility_drop_threshold:
        gates_passed.append("mobility_loss")
    else:
        gates_failed.append("mobility_loss")

    # Fire if both gates pass
    fired = len(gates_passed) == 2

    # Compute confidence
    if fired:
        # Higher confidence for worse drops
        eval_severity = min(0.5, abs(delta_eval - eval_drop_threshold) * 0.15)
        mobility_severity = min(0.3, abs(mobility_delta - mobility_drop_threshold) * 0.3)
        confidence = 0.5 + eval_severity + mobility_severity
    else:
        confidence = 0.0

    return TagEvidence(
        tag="panic_move",
        fired=fired,
        confidence=min(1.0, confidence),
        evidence=evidence,
        gates_passed=gates_passed,
        gates_failed=gates_failed,
    )


__all__ = ["detect"]
