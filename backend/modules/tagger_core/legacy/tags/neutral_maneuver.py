"""
Neutral Maneuver tag detector.

Detects when a player makes a piece repositioning move that neither
significantly improves nor worsens the position. Neutral play.

Conditions:
- Move is a maneuver candidate
- Neutral maneuver score (close to 0)
- Minimal metrics changes
- Evaluation relatively stable

Evidence:
- is_maneuver: Whether move is maneuver candidate
- maneuver_score: Near-zero quality score
- metrics: Small changes in all dimensions
"""
from ...models import TagContext, TagEvidence
from ..shared.maneuver_helpers import is_maneuver_candidate, compute_maneuver_score


def detect(ctx: TagContext) -> TagEvidence:
    """
    Detect neutral maneuver.

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
            tag="neutral_maneuver",
            fired=False,
            confidence=0.0,
            evidence=evidence,
            gates_passed=gates_passed,
            gates_failed=gates_failed,
        )

    # Gate 2: Neutral maneuver score
    if -0.2 <= maneuver_score <= 0.2:
        gates_passed.append("neutral_score")
    else:
        gates_failed.append("neutral_score")

    # Gate 3: Small metrics changes
    small_changes = (
        abs(mobility_change) < 0.1
        and abs(center_change) < 0.1
    )
    if small_changes:
        gates_passed.append("small_changes")
    else:
        gates_failed.append("small_changes")

    # Gate 4: Evaluation relatively stable
    eval_stable = -0.15 < delta_eval < 0.15
    if eval_stable:
        gates_passed.append("eval_stable")
    else:
        gates_failed.append("eval_stable")

    # Fire if all gates pass
    fired = len(gates_passed) == 4

    # Compute confidence
    if fired:
        # Moderate confidence for neutral moves
        neutrality_bonus = 0.3 * (1.0 - abs(maneuver_score) / 0.2)
        stability_bonus = 0.2 * (1.0 - abs(delta_eval) / 0.15)
        confidence = 0.5 + neutrality_bonus + stability_bonus
    else:
        confidence = 0.0

    return TagEvidence(
        tag="neutral_maneuver",
        fired=fired,
        confidence=min(1.0, confidence),
        evidence=evidence,
        gates_passed=gates_passed,
        gates_failed=gates_failed,
    )


__all__ = ["detect"]
