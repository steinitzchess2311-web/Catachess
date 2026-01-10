"""
Neutral Tension Creation tag detector.

Detects when tension is created but in an asymmetrical or weaker manner,
often in neutral evaluation ranges without clear advantage to either side.

Conditions:
- Evaluation in neutral band (-0.12 to +0.12 around zero)
- Asymmetrical mobility changes OR weaker tension signals
- Some activity increase but not strongly symmetrical

Evidence:
- mobility_self: Self mobility change
- mobility_opp: Opponent mobility change
- symmetry_gap: Difference in mobility magnitudes
- eval: Evaluation change
"""
from ...models import TagContext, TagEvidence
from ...config import NEUTRAL_TENSION_BAND
from ..shared.tension_helpers import (
    check_contact_increase,
    is_asymmetrical_tension,
)


def detect(ctx: TagContext) -> TagEvidence:
    """
    Detect neutral tension creation.

    Args:
        ctx: Tag detection context

    Returns:
        TagEvidence with detection result
    """
    gates_passed = []
    gates_failed = []
    evidence = {}

    mobility_self = ctx.component_deltas.get("mobility", 0.0)
    mobility_opp = ctx.opp_component_deltas.get("mobility", 0.0)
    asymmetrical = is_asymmetrical_tension(ctx)
    contact_increase, contact_delta = check_contact_increase(ctx)

    # Store evidence
    evidence["delta_eval"] = ctx.delta_eval
    evidence["eval_before"] = ctx.eval_before
    evidence["mobility_self"] = mobility_self
    evidence["mobility_opp"] = mobility_opp
    evidence["contact_delta"] = contact_delta
    evidence["phase"] = ctx.phase_bucket
    evidence["neutral_band_threshold"] = NEUTRAL_TENSION_BAND

    # Gate 1: Evaluation in neutral band
    neutral_eval = abs(ctx.eval_before) <= NEUTRAL_TENSION_BAND
    if neutral_eval:
        gates_passed.append("neutral_eval")
    else:
        gates_failed.append("neutral_eval")

    # Gate 2: Asymmetrical tension OR weak symmetrical
    if asymmetrical:
        gates_passed.append("asymmetrical_tension")
    else:
        gates_failed.append("asymmetrical_tension")

    # Gate 3: Some activity increase (either mobility or contact)
    has_activity = (
        abs(mobility_self) > 0.05
        or abs(mobility_opp) > 0.05
        or contact_increase
    )
    if has_activity:
        gates_passed.append("has_activity")
    else:
        gates_failed.append("has_activity")

    # Fire if neutral eval + asymmetrical + some activity
    fired = neutral_eval and asymmetrical and has_activity

    # Compute confidence
    if fired:
        # Moderate confidence for neutral tension
        activity_bonus = min(0.3, (abs(mobility_self) + abs(mobility_opp)) * 0.3)
        contact_bonus = min(0.2, contact_delta * 1.5) if contact_increase else 0
        confidence = 0.4 + activity_bonus + contact_bonus
    else:
        confidence = 0.0

    return TagEvidence(
        tag="neutral_tension_creation",
        fired=fired,
        confidence=min(1.0, confidence),
        evidence=evidence,
        gates_passed=gates_passed,
        gates_failed=gates_failed,
    )


__all__ = ["detect"]
