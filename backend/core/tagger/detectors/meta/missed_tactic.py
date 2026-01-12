"""
Missed Tactic tag detector.

Detects when a player misses a significantly better tactical opportunity,
resulting in a substantial evaluation drop.

Condition:
- delta_eval < -TACTICAL_MISS_LOSS / 100 (typically -150cp / 100 = -1.5)

Evidence:
- eval_delta: The evaluation loss
- threshold: The threshold that was exceeded
- played_move: The move that was played
- best_move: The better move that was available
"""
from core.tagger.models import TagContext, TagEvidence
from ...config import TACTICAL_MISS_LOSS


def detect(ctx: TagContext) -> TagEvidence:
    """
    Detect missed tactic.

    Args:
        ctx: Tag detection context

    Returns:
        TagEvidence with detection result
    """
    gates_passed = []
    gates_failed = []
    evidence = {}

    threshold = -TACTICAL_MISS_LOSS / 100.0  # Convert cp to pawns
    delta_eval = ctx.delta_eval

    # Store evidence values
    evidence["delta_eval"] = delta_eval
    evidence["threshold"] = threshold
    evidence["eval_drop_cp"] = int(delta_eval * 100)
    evidence["played_move"] = ctx.played_move.uci()
    evidence["best_move"] = ctx.best_move.uci()
    evidence["tactical_weight"] = ctx.tactical_weight

    # Gate: Significant evaluation drop
    if delta_eval < threshold:
        gates_passed.append("significant_eval_drop")
        fired = True
    else:
        gates_failed.append("significant_eval_drop")
        fired = False

    # Compute confidence based on how much worse the move was
    # More negative delta_eval = higher confidence in missed tactic
    if fired:
        excess_loss = abs(delta_eval) - abs(threshold)
        confidence = min(1.0, 0.6 + excess_loss * 0.4)
    else:
        confidence = 0.0

    return TagEvidence(
        tag="missed_tactic",
        fired=fired,
        confidence=confidence,
        evidence=evidence,
        gates_passed=gates_passed,
        gates_failed=gates_failed,
    )


__all__ = ["detect"]
