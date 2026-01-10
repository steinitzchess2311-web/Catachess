"""
Failed Prophylactic tag detector.

Detects failed prophylaxis attempts - moves with clear prophylactic intent
that fail to neutralize threats and result in evaluation loss.

This is distinct from prophylactic_meaningless in that it requires:
- Clear prophylactic pattern (bishop retreat, knight reposition, etc.)
- Opponent's tactical pressure remains high despite the prophylactic attempt
- Significant evaluation loss

Conditions:
- Move is prophylactic candidate
- Preventive intent (positive preventive score)
- Opponent's tactics remain high after the move
- Evaluation loss

Evidence:
- is_candidate: Whether move passes prophylaxis gates
- preventive_score: Attempted opponent restriction
- opp_tactics_after: Opponent's tactics after move (still high)
- eval_loss: Evaluation dropped significantly
"""
from ...models import TagContext, TagEvidence
from ..shared.prophylaxis_helpers import (
    is_prophylaxis_candidate,
    compute_preventive_score,
)


# Thresholds
MIN_PREVENTIVE_INTENT = 0.05  # Some prophylactic intent required
OPP_TACTICS_THRESHOLD = 0.3  # Opponent tactics still high
EVAL_DROP_THRESHOLD = -0.5  # 50cp loss


def detect(ctx: TagContext) -> TagEvidence:
    """
    Detect failed prophylactic attempt.

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
            tag="failed_prophylactic",
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

    opp_tactics_after = ctx.opp_metrics_played.get("tactics", 0.0)
    delta_eval = ctx.delta_eval

    # Store evidence
    evidence.update({
        "preventive_score": preventive_score,
        "opp_tactics_after": opp_tactics_after,
        "delta_eval": delta_eval,
    })
    evidence.update(preventive_data)

    # Gate 2: Prophylactic intent (attempted restriction)
    has_intent = preventive_score >= MIN_PREVENTIVE_INTENT
    if has_intent:
        gates_passed.append("prophylactic_intent")
    else:
        gates_failed.append("prophylactic_intent")

    # Gate 3: Opponent tactics remain high (threat not neutralized)
    threat_remains = opp_tactics_after >= OPP_TACTICS_THRESHOLD
    evidence["threat_remains"] = threat_remains

    if threat_remains:
        gates_passed.append("threat_remains")
    else:
        gates_failed.append("threat_remains")

    # Gate 4: Evaluation loss
    eval_loss = delta_eval <= EVAL_DROP_THRESHOLD
    evidence["eval_loss"] = eval_loss

    if eval_loss:
        gates_passed.append("eval_loss")
    else:
        gates_failed.append("eval_loss")

    # Fire if all gates pass
    fired = len(gates_passed) == 4

    # Compute confidence
    if fired:
        # Higher confidence for worse failures
        loss_magnitude = abs(delta_eval) - abs(EVAL_DROP_THRESHOLD)
        loss_bonus = min(0.3, loss_magnitude * 0.3)
        threat_bonus = min(0.2, (opp_tactics_after - OPP_TACTICS_THRESHOLD) * 0.5)
        confidence = 0.6 + loss_bonus + threat_bonus
    else:
        confidence = 0.0

    return TagEvidence(
        tag="failed_prophylactic",
        fired=fired,
        confidence=min(1.0, confidence),
        evidence=evidence,
        gates_passed=gates_passed,
        gates_failed=gates_failed,
    )


__all__ = ["detect"]
