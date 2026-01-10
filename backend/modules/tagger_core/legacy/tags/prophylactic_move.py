"""
Prophylactic Move tag detector.

Detects generic prophylactic moves - anticipatory moves that prevent opponent
threats or restrict opponent play. This is the base prophylaxis tag, which gets
suppressed when more specific quality tags (direct/latent/meaningless) fire.

Conditions:
- Move is a prophylaxis candidate (non-forcing, non-reactive)
- Preventive score >= threshold (opponent restriction)
- Prophylactic signal (threat response + consolidation)

Prophylactic signal requires:
- Opponent restrained (mobility/tactics drop) OR
- Self solidified (structure/center gain)

Evidence:
- is_candidate: Whether move passes prophylaxis gates
- preventive_score: Opponent restriction score
- opp_restrained: Opponent mobility/tactics dropping
- self_solidified: Structure or center improving
"""
from ...models import TagContext, TagEvidence
from ..shared.prophylaxis_helpers import (
    is_prophylaxis_candidate,
    compute_preventive_score,
    PREVENTIVE_TRIGGER,
    STRUCTURE_MIN,
)


def detect(ctx: TagContext) -> TagEvidence:
    """
    Detect generic prophylactic move.

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
    if is_candidate:
        gates_passed.append("is_candidate")
    else:
        gates_failed.append("is_candidate")
        return TagEvidence(
            tag="prophylactic_move",
            fired=False,
            confidence=0.0,
            evidence=evidence,
            gates_passed=gates_passed,
            gates_failed=gates_failed,
        )

    # Compute preventive and consolidation scores
    preventive_data = compute_preventive_score(ctx)
    preventive_score = preventive_data["preventive_score"]
    opp_restrained = preventive_data["opp_restrained"]

    structure_delta = ctx.component_deltas.get("structure", 0.0)
    center_delta = ctx.component_deltas.get("center_control", 0.0)
    king_safety_delta = ctx.component_deltas.get("king_safety", 0.0)
    mobility_delta = ctx.component_deltas.get("mobility", 0.0)

    # Self solidification: structure gain or center gain
    self_solidified = (structure_delta >= 0.0) or (center_delta >= 0.05)

    # Store evidence
    evidence.update({
        "preventive_score": preventive_score,
        "opp_restrained": opp_restrained,
        "self_solidified": self_solidified,
        "structure_delta": structure_delta,
        "king_safety_delta": king_safety_delta,
        "mobility_delta": mobility_delta,
        "center_delta": center_delta,
    })
    evidence.update(preventive_data)

    # Gate 2: Preventive score >= trigger
    if preventive_score >= PREVENTIVE_TRIGGER:
        gates_passed.append("preventive_trigger")
    else:
        gates_failed.append("preventive_trigger")

    # Gate 3: Prophylactic signal (opponent restrained AND self solidified)
    prophylactic_signal = opp_restrained and self_solidified
    if prophylactic_signal:
        gates_passed.append("prophylactic_signal")
    else:
        gates_failed.append("prophylactic_signal")

    # Fire if all gates pass
    fired = len(gates_passed) == 3

    # Compute confidence
    if fired:
        # Base confidence
        score_bonus = min(0.4, (preventive_score - PREVENTIVE_TRIGGER) * 1.5)
        structure_bonus = min(0.2, structure_delta * 0.8) if structure_delta > 0 else 0
        center_bonus = min(0.1, center_delta * 0.5) if center_delta > 0 else 0
        confidence = 0.5 + score_bonus + structure_bonus + center_bonus
    else:
        confidence = 0.0

    return TagEvidence(
        tag="prophylactic_move",
        fired=fired,
        confidence=min(1.0, confidence),
        evidence=evidence,
        gates_passed=gates_passed,
        gates_failed=gates_failed,
    )


__all__ = ["detect"]
