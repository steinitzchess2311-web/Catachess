"""
Prophylactic Latent tag detector.

Detects softer positional prophylaxis - latent prevention without clear
tactical signals. Subtler than prophylactic_direct.

Conditions:
- Move is prophylactic (passes prophylactic_move gates)
- Preventive score at or near trigger
- Does NOT meet direct gate criteria
- Moderate soft positioning or preventive signals

Latent prophylaxis is characterized by:
- Lower preventive scores (near trigger but not high)
- Moderate soft positioning (below direct threshold)
- Still shows opponent restriction or self-consolidation

Evidence:
- preventive_score: Opponent restriction score
- soft_weight: Self-consolidation score
- latent_quality: Whether meets latent (not direct) criteria
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
    Detect latent prophylaxis.

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
            tag="prophylactic_latent",
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

    # Gate 4: NOT direct quality (must be latent, not direct)
    direct_gate = (
        preventive_score >= (PREVENTIVE_TRIGGER + 0.02)
        or (soft_weight >= 0.65 and tactical_weight <= 0.6)
    )
    latent_quality = not direct_gate
    evidence["direct_gate"] = direct_gate
    evidence["latent_quality"] = latent_quality

    if latent_quality:
        gates_passed.append("latent_quality")
    else:
        gates_failed.append("latent_quality")

    # Fire if all gates pass
    fired = len(gates_passed) == 4

    # Compute confidence
    if fired:
        # Moderate confidence for latent prophylaxis
        preventive_bonus = min(0.2, preventive_score * 1.0)
        soft_bonus = min(0.15, soft_weight * 0.6)
        confidence = 0.55 + preventive_bonus + soft_bonus
    else:
        confidence = 0.0

    return TagEvidence(
        tag="prophylactic_latent",
        fired=fired,
        confidence=min(1.0, confidence),
        evidence=evidence,
        gates_passed=gates_passed,
        gates_failed=gates_failed,
    )


__all__ = ["detect"]
