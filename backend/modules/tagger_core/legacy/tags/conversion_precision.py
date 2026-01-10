"""
Conversion Precision tag detector.

Detects when a player maintains a winning evaluation while converting
an advantage (e.g., in an endgame or simplified position).

Conditions:
- eval_before >= +2.0 pawns (winning advantage)
- delta_eval >= -0.15 pawns (maintains evaluation, small loss allowed)

Evidence:
- eval_before: Evaluation before the move
- delta_eval: Evaluation change
- phase: Game phase (often endgame)
"""
from ...models import TagContext, TagEvidence


def detect(ctx: TagContext) -> TagEvidence:
    """
    Detect conversion precision.

    Args:
        ctx: Tag detection context

    Returns:
        TagEvidence with detection result
    """
    gates_passed = []
    gates_failed = []
    evidence = {}

    # Thresholds
    winning_threshold = 2.0  # +2 pawns advantage
    maintain_threshold = -0.15  # Allow small eval loss

    eval_before = ctx.eval_before
    delta_eval = ctx.delta_eval

    # Store evidence
    evidence["eval_before"] = eval_before
    evidence["delta_eval"] = delta_eval
    evidence["eval_played"] = ctx.eval_played
    evidence["phase"] = ctx.phase_bucket
    evidence["winning_threshold"] = winning_threshold
    evidence["maintain_threshold"] = maintain_threshold

    # Gate 1: Winning position
    if eval_before >= winning_threshold:
        gates_passed.append("winning_position")
    else:
        gates_failed.append("winning_position")

    # Gate 2: Maintained evaluation (small loss allowed)
    if delta_eval >= maintain_threshold:
        gates_passed.append("maintained_evaluation")
    else:
        gates_failed.append("maintained_evaluation")

    # Fire if both gates pass
    fired = len(gates_passed) == 2

    # Compute confidence
    if fired:
        # Higher confidence for better maintenance and larger advantage
        advantage_bonus = min(0.3, (eval_before - winning_threshold) * 0.1)
        maintenance_bonus = min(0.3, (delta_eval - maintain_threshold) * 0.5)
        confidence = 0.4 + advantage_bonus + maintenance_bonus
    else:
        confidence = 0.0

    return TagEvidence(
        tag="conversion_precision",
        fired=fired,
        confidence=min(1.0, confidence),
        evidence=evidence,
        gates_passed=gates_passed,
        gates_failed=gates_failed,
    )


__all__ = ["detect"]
