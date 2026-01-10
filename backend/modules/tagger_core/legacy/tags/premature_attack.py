"""
Premature Attack tag detector.

Detects when a player attempts to create tension or attack but with poor
timing, resulting in unfavorable evaluation loss.

Conditions:
- Attempt to increase activity (mobility or contact)
- Significant evaluation loss (below TENSION_EVAL_MIN, typically -0.9)
- Activity increase present but evaluation suggests poor timing

Evidence:
- delta_eval: Evaluation change
- mobility_delta: Mobility change
- contact_delta: Contact ratio change
- tactical_weight: Position tactical complexity
"""
from ...models import TagContext, TagEvidence
from ...config import TENSION_EVAL_MIN
from ..shared.tension_helpers import check_contact_increase


def detect(ctx: TagContext) -> TagEvidence:
    """
    Detect premature attack.

    Args:
        ctx: Tag detection context

    Returns:
        TagEvidence with detection result
    """
    gates_passed = []
    gates_failed = []
    evidence = {}

    mobility_delta = ctx.component_deltas.get("mobility", 0.0)
    contact_increase, contact_delta = check_contact_increase(ctx)
    delta_eval = ctx.delta_eval

    # Store evidence
    evidence["delta_eval"] = delta_eval
    evidence["mobility_delta"] = mobility_delta
    evidence["contact_delta"] = contact_delta
    evidence["tactical_weight"] = ctx.tactical_weight
    evidence["threshold"] = TENSION_EVAL_MIN
    evidence["phase"] = ctx.phase_bucket

    # Gate 1: Significant evaluation loss (premature/poor timing)
    if delta_eval < TENSION_EVAL_MIN:
        gates_passed.append("significant_eval_loss")
    else:
        gates_failed.append("significant_eval_loss")

    # Gate 2: Attempted activity increase
    attempted_activity = (
        mobility_delta > 0.1  # Attempted mobility increase
        or contact_increase   # Or contact increase
    )
    if attempted_activity:
        gates_passed.append("attempted_activity")
    else:
        gates_failed.append("attempted_activity")

    # Gate 3: In opening/middlegame (premature attacks less likely in endgame)
    early_phase = ctx.phase_ratio > 0.3
    if early_phase:
        gates_passed.append("early_phase")
    else:
        gates_failed.append("early_phase")

    # Fire if eval loss + attempted activity + early phase
    fired = len(gates_passed) == 3

    # Compute confidence
    if fired:
        # Higher confidence for worse eval loss and more activity
        eval_severity = min(0.4, abs(delta_eval - TENSION_EVAL_MIN) * 0.5)
        activity_bonus = min(0.3, max(mobility_delta, contact_delta) * 1.5)
        confidence = 0.5 + eval_severity + activity_bonus
    else:
        confidence = 0.0

    return TagEvidence(
        tag="premature_attack",
        fired=fired,
        confidence=min(1.0, confidence),
        evidence=evidence,
        gates_passed=gates_passed,
        gates_failed=gates_failed,
    )


__all__ = ["detect"]
