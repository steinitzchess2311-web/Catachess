"""
Inaccurate Tactical Sacrifice tag detector.

Detects dubious tactical sacrifices - material sacrificed to attack the
opponent's king but with insufficient compensation.

Conditions:
- Move is a sacrifice (material loss ≥ 0.5 pawns)
- Opponent king safety drops significantly (≤ -0.1)
- Evaluation loss is excessive (> 0.6 pawns)

This represents tactical attacks that give up too much material without
adequate compensation. The attack exists but is unsound.

Evidence:
- is_sacrifice: Whether move sacrifices material
- material_delta: Material loss in pawns
- king_drop: Opponent king safety delta
- eval_loss: Evaluation loss (excessive)
- unsound: Whether compensation is insufficient
"""
from ...models import TagContext, TagEvidence
from ..shared.sacrifice_helpers import (
    is_sacrifice_candidate,
    SACRIFICE_EVAL_TOLERANCE,
    SACRIFICE_KING_DROP_THRESHOLD,
)


def detect(ctx: TagContext) -> TagEvidence:
    """
    Detect inaccurate tactical sacrifice.

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
            tag="inaccurate_tactical_sacrifice",
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

    # Gate 2: King safety drop (attack exists)
    king_attack = king_drop <= SACRIFICE_KING_DROP_THRESHOLD
    if king_attack:
        gates_passed.append("king_attack")
    else:
        gates_failed.append("king_attack")

    # Gate 3: Insufficient compensation (eval loss too high)
    insufficient_compensation = eval_loss > SACRIFICE_EVAL_TOLERANCE
    evidence["unsound"] = insufficient_compensation

    if insufficient_compensation:
        gates_passed.append("insufficient_compensation")
    else:
        gates_failed.append("insufficient_compensation")

    # Fire if all gates pass
    fired = len(gates_passed) == 3

    # Compute confidence
    if fired:
        # Higher confidence for worse sacrifices (bigger eval drops)
        loss_magnitude = eval_loss - SACRIFICE_EVAL_TOLERANCE
        loss_bonus = min(0.3, loss_magnitude * 0.3)
        king_bonus = min(0.2, abs(king_drop + SACRIFICE_KING_DROP_THRESHOLD) * 0.5)
        confidence = 0.6 + loss_bonus + king_bonus
    else:
        confidence = 0.0

    return TagEvidence(
        tag="inaccurate_tactical_sacrifice",
        fired=fired,
        confidence=min(1.0, confidence),
        evidence=evidence,
        gates_passed=gates_passed,
        gates_failed=gates_failed,
    )


__all__ = ["detect"]
