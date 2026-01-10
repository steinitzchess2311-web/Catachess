"""
Constructive Maneuver tag detector.

Detects when a player makes a good piece repositioning move that improves
position metrics (mobility, center control) with minimal evaluation cost.

Conditions:
- Move is a maneuver candidate (minor piece, quiet, non-capture)
- Positive maneuver score (metrics improve)
- Evaluation cost acceptable (delta_eval > -0.3)

Evidence:
- is_maneuver: Whether move is maneuver candidate
- maneuver_score: Quality of the maneuver
- metrics improvements: Mobility, center control changes
"""
from ...models import TagContext, TagEvidence
from ..shared.maneuver_helpers import is_maneuver_candidate, compute_maneuver_score


def detect(ctx: TagContext) -> TagEvidence:
    """
    Detect constructive maneuver.

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

    mobility_gain = ctx.component_deltas.get("mobility", 0.0)
    center_gain = ctx.component_deltas.get("center_control", 0.0)
    delta_eval = ctx.delta_eval

    # Store evidence
    evidence["is_maneuver_candidate"] = is_maneuver
    evidence["maneuver_score"] = maneuver_score
    evidence["mobility_gain"] = mobility_gain
    evidence["center_gain"] = center_gain
    evidence["delta_eval"] = delta_eval
    evidence["phase"] = ctx.phase_bucket

    # Gate 1: Is maneuver candidate
    if is_maneuver:
        gates_passed.append("is_maneuver")
    else:
        gates_failed.append("is_maneuver")
        return TagEvidence(
            tag="constructive_maneuver",
            fired=False,
            confidence=0.0,
            evidence=evidence,
            gates_passed=gates_passed,
            gates_failed=gates_failed,
        )

    # Gate 2: Positive maneuver score
    if maneuver_score > 0.2:
        gates_passed.append("positive_score")
    else:
        gates_failed.append("positive_score")

    # Gate 3: Acceptable evaluation cost
    if delta_eval > -0.3:
        gates_passed.append("acceptable_eval")
    else:
        gates_failed.append("acceptable_eval")

    # Gate 4: Some metric improvement
    metrics_improve = mobility_gain > 0.05 or center_gain > 0.05
    if metrics_improve:
        gates_passed.append("metrics_improve")
    else:
        gates_failed.append("metrics_improve")

    # Fire if all gates pass
    fired = len(gates_passed) == 4

    # Compute confidence
    if fired:
        score_bonus = min(0.4, maneuver_score * 0.6)
        metrics_bonus = min(0.3, (mobility_gain + center_gain) * 0.8)
        eval_bonus = min(0.2, (delta_eval + 0.3) * 0.5)
        confidence = 0.4 + score_bonus + metrics_bonus + eval_bonus
    else:
        confidence = 0.0

    return TagEvidence(
        tag="constructive_maneuver",
        fired=fired,
        confidence=min(1.0, confidence),
        evidence=evidence,
        gates_passed=gates_passed,
        gates_failed=gates_failed,
    )


__all__ = ["detect"]
