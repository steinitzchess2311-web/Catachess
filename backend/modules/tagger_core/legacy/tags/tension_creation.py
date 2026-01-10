"""
Tension Creation tag detector.

Detects when a player creates tension through symmetrical activity increase,
where both sides increase mobility and/or contact ratio increases.

Conditions:
- Evaluation in acceptable range (TENSION_EVAL_MIN to TENSION_EVAL_MAX)
- Symmetrical mobility increase (both players increase similarly)
- OR significant contact ratio increase
- Sufficient mobility magnitudes

Evidence:
- mobility_self: Self mobility change
- mobility_opp: Opponent mobility change
- symmetry_gap: Difference in mobility magnitudes
- contact_delta: Contact ratio change
- eval_band: Whether eval is in acceptable range
"""
from ...models import TagContext, TagEvidence
from ..shared.tension_helpers import (
    check_symmetry_condition,
    check_contact_increase,
    check_eval_band,
    mobility_magnitudes_sufficient,
)


def detect(ctx: TagContext) -> TagEvidence:
    """
    Detect tension creation.

    Args:
        ctx: Tag detection context

    Returns:
        TagEvidence with detection result
    """
    gates_passed = []
    gates_failed = []
    evidence = {}

    # Check conditions
    eval_ok = check_eval_band(ctx)
    symmetry_ok, symmetry_gap = check_symmetry_condition(ctx)
    contact_increase, contact_delta = check_contact_increase(ctx)
    mobility_ok = mobility_magnitudes_sufficient(ctx)

    mobility_self = ctx.component_deltas.get("mobility", 0.0)
    mobility_opp = ctx.opp_component_deltas.get("mobility", 0.0)

    # Store evidence
    evidence["delta_eval"] = ctx.delta_eval
    evidence["mobility_self"] = mobility_self
    evidence["mobility_opp"] = mobility_opp
    evidence["symmetry_gap"] = symmetry_gap
    evidence["contact_delta"] = contact_delta
    evidence["phase"] = ctx.phase_bucket

    # Gate 1: Evaluation in acceptable range
    if eval_ok:
        gates_passed.append("eval_in_range")
    else:
        gates_failed.append("eval_in_range")

    # Gate 2: Either symmetrical mobility OR contact increase
    if symmetry_ok and mobility_ok:
        gates_passed.append("symmetrical_mobility")
    elif contact_increase:
        gates_passed.append("contact_increase")
    else:
        gates_failed.append("symmetrical_mobility_or_contact")

    # Gate 3: Sufficient activity (at least one source)
    if mobility_ok or contact_increase:
        gates_passed.append("sufficient_activity")
    else:
        gates_failed.append("sufficient_activity")

    # Fire if eval OK and (symmetry OR contact) and sufficient activity
    fired = (
        eval_ok
        and (symmetry_ok or contact_increase)
        and (mobility_ok or contact_increase)
    )

    # Compute confidence
    if fired:
        # Higher confidence for better symmetry and more activity
        symmetry_bonus = 0.3 if symmetry_ok else 0.1
        contact_bonus = min(0.3, contact_delta * 2.0) if contact_increase else 0
        mobility_bonus = min(0.2, (mobility_self + mobility_opp) * 0.5)
        confidence = 0.4 + symmetry_bonus + contact_bonus + mobility_bonus
    else:
        confidence = 0.0

    return TagEvidence(
        tag="tension_creation",
        fired=fired,
        confidence=min(1.0, confidence),
        evidence=evidence,
        gates_passed=gates_passed,
        gates_failed=gates_failed,
    )


__all__ = ["detect"]
