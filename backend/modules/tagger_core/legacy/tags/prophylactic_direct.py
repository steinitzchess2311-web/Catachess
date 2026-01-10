"""
Prophylactic Direct tag detector.

Detects strong tactical prophylaxis - direct prevention of opponent threats
with clear tactical signals. This is the highest quality prophylaxis tag.

Conditions:
- Move is prophylactic (passes prophylactic_move gates)
- High preventive score (≥ trigger + margin)
- OR high soft weight (≥ 0.65) with low tactical weight
- Clear defensive consolidation

Direct gate triggers on:
- Preventive score well above trigger (≥ 0.18)
- OR soft positioning very strong (≥ 0.65) with tactical_weight ≤ 0.6

Evidence:
- preventive_score: Opponent restriction score
- soft_weight: Self-consolidation score
- tactical_weight: Position tactical complexity
- direct_gate: Whether direct criteria met
"""
from ...models import TagContext, TagEvidence
from ..shared.prophylaxis_helpers import (
    is_prophylaxis_candidate,
    compute_preventive_score,
    compute_soft_weight,
    PREVENTIVE_TRIGGER,
)


def detect(ctx: TagContext) -> TagEvidence:
    """
    Detect direct prophylaxis.

    Args:
        ctx: Tag detection context

    Returns:
        TagEvidence with detection result
    """
    gates_passed = []
    gates_failed = []
    evidence = {}

    is_candidate = is_prophylaxis_candidate(ctx)
    evidence["is_candidate"] = is_candidate

    # Gate 1: Is prophylaxis candidate
    if not is_candidate:
        gates_failed.append("is_candidate")
        return TagEvidence(
            tag="prophylactic_direct",
            fired=False,
            confidence=0.0,
            evidence=evidence,
            gates_passed=gates_passed,
            gates_failed=gates_failed,
        )
    gates_passed.append("is_candidate")

    # Compute scores
    preventive_data = compute_preventive_score(ctx)
    preventive_score = preventive_data["preventive_score"]
    opp_restrained = preventive_data["opp_restrained"]

    soft_weight = compute_soft_weight(ctx)
    tactical_weight = ctx.tactical_weight

    structure_delta = ctx.component_deltas.get("structure", 0.0)
    center_delta = ctx.component_deltas.get("center_control", 0.0)
    self_solidified = (structure_delta >= 0.0) or (center_delta >= 0.05)

    # Store evidence
    evidence.update({
        "preventive_score": preventive_score,
        "soft_weight": soft_weight,
        "tactical_weight": tactical_weight,
        "opp_restrained": opp_restrained,
        "self_solidified": self_solidified,
    })
    evidence.update(preventive_data)

    # Gate 2: Preventive score above trigger
    if preventive_score >= PREVENTIVE_TRIGGER:
        gates_passed.append("preventive_trigger")
    else:
        gates_failed.append("preventive_trigger")

    # Gate 3: Prophylactic signal
    prophylactic_signal = opp_restrained and self_solidified
    if prophylactic_signal:
        gates_passed.append("prophylactic_signal")
    else:
        gates_failed.append("prophylactic_signal")

    # Gate 4: Direct quality criteria
    direct_gate = (
        preventive_score >= (PREVENTIVE_TRIGGER + 0.02)  # 0.18+
        or (soft_weight >= 0.65 and tactical_weight <= 0.6)
    )
    evidence["direct_gate"] = direct_gate

    if direct_gate:
        gates_passed.append("direct_gate")
    else:
        gates_failed.append("direct_gate")

    # Fire if all gates pass
    fired = len(gates_passed) == 4

    # Compute confidence
    if fired:
        # Higher confidence for stronger signals
        preventive_bonus = min(0.3, preventive_score * 1.2)
        soft_bonus = min(0.2, soft_weight * 0.8)
        confidence = 0.6 + preventive_bonus + soft_bonus
    else:
        confidence = 0.0

    return TagEvidence(
        tag="prophylactic_direct",
        fired=fired,
        confidence=min(1.0, confidence),
        evidence=evidence,
        gates_passed=gates_passed,
        gates_failed=gates_failed,
    )


__all__ = ["detect"]
