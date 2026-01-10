"""
Positional Sacrifice tag detector.

Detects sound positional sacrifices - material sacrificed for positional
compensation (structure, space, initiative) without direct king attack.

Conditions:
- Move is a sacrifice (material loss ≥ 0.5 pawns)
- No significant opponent king safety drop (> -0.1)
- Evaluation loss is acceptable (≤ 0.6 pawns)

This represents sacrifices for long-term positional advantages rather than
immediate tactical threats.

Evidence:
- is_sacrifice: Whether move sacrifices material
- material_delta: Material loss in pawns
- king_drop: Opponent king safety delta (small)
- eval_loss: Evaluation loss
- sound: Whether compensation is acceptable
"""
from ...models import TagContext, TagEvidence
from ..shared.sacrifice_helpers import (
    is_sacrifice_candidate,
    SACRIFICE_EVAL_TOLERANCE,
    SACRIFICE_KING_DROP_THRESHOLD,
)


def detect(ctx: TagContext) -> TagEvidence:
    """
    Detect positional sacrifice.

    Args:
        ctx: Tag detection context

    Returns:
        TagEvidence with detection result
    """
    gates_passed = []
    gates_failed = []
    evidence = {}

    # Check if move is sacrifice
    is_sacrifice, sacrifice_evidence = is_sacrifice_candidate(ctx)
    evidence.update(sacrifice_evidence)
    evidence["is_sacrifice"] = is_sacrifice

    # Gate 1: Is sacrifice
    if is_sacrifice:
        gates_passed.append("is_sacrifice")
    else:
        gates_failed.append("is_sacrifice")
        return TagEvidence(
            tag="positional_sacrifice",
            fired=False,
            confidence=0.0,
            evidence=evidence,
            gates_passed=gates_passed,
            gates_failed=gates_failed,
        )

    # Compute opponent king safety drop
    opp_king_before = ctx.opp_metrics_before.get("king_safety", 0.0)
    opp_king_after = ctx.opp_metrics_played.get("king_safety", 0.0)
    king_drop = opp_king_after - opp_king_before

    # Compute evaluation loss
    eval_loss = abs(ctx.delta_eval)

    # Store evidence
    evidence["opp_king_before"] = opp_king_before
    evidence["opp_king_after"] = opp_king_after
    evidence["king_drop"] = king_drop
    evidence["eval_loss"] = eval_loss

    # Gate 2: NO significant king attack
    no_king_attack = king_drop > SACRIFICE_KING_DROP_THRESHOLD
    if no_king_attack:
        gates_passed.append("no_king_attack")
    else:
        gates_failed.append("no_king_attack")

    # Gate 3: Sound compensation (eval loss acceptable)
    sound_compensation = eval_loss <= SACRIFICE_EVAL_TOLERANCE
    evidence["sound"] = sound_compensation

    if sound_compensation:
        gates_passed.append("sound_compensation")
    else:
        gates_failed.append("sound_compensation")

    # Fire if all gates pass
    fired = len(gates_passed) == 3

    # Compute confidence
    if fired:
        # Higher confidence for smaller eval drops
        # Lower confidence if king_drop is close to threshold (ambiguous)
        compensation_bonus = min(0.3, (SACRIFICE_EVAL_TOLERANCE - eval_loss) * 0.5)
        clarity_bonus = 0.2 if king_drop > 0.0 else 0.1
        confidence = 0.6 + compensation_bonus + clarity_bonus
    else:
        confidence = 0.0

    return TagEvidence(
        tag="positional_sacrifice",
        fired=fired,
        confidence=min(1.0, confidence),
        evidence=evidence,
        gates_passed=gates_passed,
        gates_failed=gates_failed,
    )


__all__ = ["detect"]
