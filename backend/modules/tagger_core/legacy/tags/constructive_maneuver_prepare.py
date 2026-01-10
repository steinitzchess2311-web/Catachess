"""
Constructive Maneuver Prepare tag detector.

Detects preparatory maneuvers that set up future improvements, even if
immediate metrics don't show large gains. Often seen in prophylactic play
or setup moves.

Conditions:
- Move is a maneuver candidate
- Small immediate metric changes
- No significant evaluation loss
- In opening/middlegame (preparation more common)

Evidence:
- is_maneuver: Whether move is maneuver candidate
- mobility_change: Small mobility change
- eval_change: Evaluation stability
"""
from ...models import TagContext, TagEvidence
from ..shared.maneuver_helpers import is_maneuver_candidate


def detect(ctx: TagContext) -> TagEvidence:
    """
    Detect preparatory maneuver.

    Args:
        ctx: Tag detection context

    Returns:
        TagEvidence with detection result
    """
    gates_passed = []
    gates_failed = []
    evidence = {}

    is_maneuver = is_maneuver_candidate(ctx)
    mobility_change = ctx.component_deltas.get("mobility", 0.0)
    center_change = ctx.component_deltas.get("center_control", 0.0)
    delta_eval = ctx.delta_eval

    # Store evidence
    evidence["is_maneuver_candidate"] = is_maneuver
    evidence["mobility_change"] = mobility_change
    evidence["center_change"] = center_change
    evidence["delta_eval"] = delta_eval
    evidence["phase"] = ctx.phase_bucket
    evidence["phase_ratio"] = ctx.phase_ratio

    # Gate 1: Is maneuver candidate
    if is_maneuver:
        gates_passed.append("is_maneuver")
    else:
        gates_failed.append("is_maneuver")
        return TagEvidence(
            tag="constructive_maneuver_prepare",
            fired=False,
            confidence=0.0,
            evidence=evidence,
            gates_passed=gates_passed,
            gates_failed=gates_failed,
        )

    # Gate 2: Small immediate metrics change (preparatory)
    small_change = abs(mobility_change) < 0.15 and abs(center_change) < 0.15
    if small_change:
        gates_passed.append("small_immediate_change")
    else:
        gates_failed.append("small_immediate_change")

    # Gate 3: Maintains evaluation (no significant loss)
    eval_stable = delta_eval > -0.2
    if eval_stable:
        gates_passed.append("eval_stable")
    else:
        gates_failed.append("eval_stable")

    # Gate 4: In opening/middlegame (preparation phase)
    preparation_phase = ctx.phase_ratio > 0.4
    if preparation_phase:
        gates_passed.append("preparation_phase")
    else:
        gates_failed.append("preparation_phase")

    # Fire if all gates pass
    fired = len(gates_passed) == 4

    # Compute confidence
    if fired:
        # Moderate confidence for preparatory moves
        phase_bonus = min(0.3, (ctx.phase_ratio - 0.4) * 0.8)
        stability_bonus = min(0.3, (delta_eval + 0.2) * 1.2)
        confidence = 0.5 + phase_bonus + stability_bonus
    else:
        confidence = 0.0

    return TagEvidence(
        tag="constructive_maneuver_prepare",
        fired=fired,
        confidence=min(1.0, confidence),
        evidence=evidence,
        gates_passed=gates_passed,
        gates_failed=gates_failed,
    )


__all__ = ["detect"]
