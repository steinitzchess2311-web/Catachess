"""
Misplaced Maneuver tag detector.

Detects when a player makes a piece repositioning move that worsens the
position, either through poor square choice or bad timing.

Conditions:
- Move is a maneuver candidate
- Negative maneuver score (metrics decline)
- Evaluation loss
- Metrics show worsening position

Evidence:
- is_maneuver: Whether move is maneuver candidate
- maneuver_score: Negative quality score
- mobility_loss: Mobility decrease
- eval_loss: Evaluation decrease
"""
from ...models import TagContext, TagEvidence
from ..shared.maneuver_helpers import is_maneuver_candidate, compute_maneuver_score


def detect(ctx: TagContext) -> TagEvidence:
    """
    Detect misplaced maneuver.

    Args:
        ctx: Tag detection context

    Returns:
        TagEvidence with detection result
    """
    gates_passed = []
    gates_failed = []
    evidence = {}

    is_maneuver = is_maneuver_candidate(ctx)
    scores = compute_maneuver_score(ctx) if is_maneuver else {}
    maneuver_score = scores.get("maneuver_score", 0.0)

    mobility_change = ctx.component_deltas.get("mobility", 0.0)
    center_change = ctx.component_deltas.get("center_control", 0.0)
    delta_eval = ctx.delta_eval

    # Store evidence
    evidence["is_maneuver_candidate"] = is_maneuver
    evidence["maneuver_score"] = maneuver_score
    evidence["mobility_change"] = mobility_change
    evidence["center_change"] = center_change
    evidence["delta_eval"] = delta_eval
    evidence["phase"] = ctx.phase_bucket

    # Gate 1: Is maneuver candidate
    if is_maneuver:
        gates_passed.append("is_maneuver")
    else:
        gates_failed.append("is_maneuver")
        return TagEvidence(
            tag="misplaced_maneuver",
            fired=False,
            confidence=0.0,
            evidence=evidence,
            gates_passed=gates_passed,
            gates_failed=gates_failed,
        )

    # Gate 2: Negative maneuver score
    if maneuver_score < -0.2:
        gates_passed.append("negative_score")
    else:
        gates_failed.append("negative_score")

    # Gate 3: Evaluation loss OR metrics decline
    eval_loss = delta_eval < -0.2
    metrics_decline = mobility_change < -0.05 or center_change < -0.05

    if eval_loss or metrics_decline:
        gates_passed.append("position_worsening")
        if eval_loss:
            evidence["eval_loss"] = True
        if metrics_decline:
            evidence["metrics_decline"] = True
    else:
        gates_failed.append("position_worsening")

    # Fire if maneuver + negative score + worsening
    fired = len(gates_passed) == 3

    # Compute confidence
    if fired:
        # Higher confidence for worse maneuvers
        score_penalty = min(0.4, abs(maneuver_score + 0.2) * 0.8)
        eval_penalty = min(0.3, abs(delta_eval + 0.2) * 0.6) if eval_loss else 0
        metrics_penalty = min(0.2, abs(mobility_change) * 2.0) if metrics_decline else 0
        confidence = 0.4 + score_penalty + eval_penalty + metrics_penalty
    else:
        confidence = 0.0

    return TagEvidence(
        tag="misplaced_maneuver",
        fired=fired,
        confidence=min(1.0, confidence),
        evidence=evidence,
        gates_passed=gates_passed,
        gates_failed=gates_failed,
    )


__all__ = ["detect"]
