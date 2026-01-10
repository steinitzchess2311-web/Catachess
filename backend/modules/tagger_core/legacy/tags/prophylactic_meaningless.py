"""
Prophylactic Meaningless tag detector.

Detects ineffective prophylaxis - moves with prophylactic intent that fail
to achieve their goal and result in evaluation loss.

Conditions:
- Move is prophylactic candidate
- Preventive signals present (opponent restriction attempt)
- BUT evaluation loss (significant drop)
- In neutral evaluation band (not winning/losing)

Meaningless prophylaxis occurs when:
- Player attempts prophylaxis but misjudges the position
- Move restricts opponent but damages own position more
- Prophylactic intent without prophylactic effect

Evidence:
- preventive_score: Opponent restriction attempt
- delta_eval: Evaluation change (negative)
- eval_loss: Significant evaluation drop
- eval_band: Position evaluation context
"""
from ...models import TagContext, TagEvidence
from ..shared.prophylaxis_helpers import (
    is_prophylaxis_candidate,
    compute_preventive_score,
    PREVENTIVE_TRIGGER,
)


# Thresholds
FAIL_EVAL_BAND_CP = 200  # ±2.00 pawns
FAIL_DROP_CP = 50  # 0.50 pawns loss


def detect(ctx: TagContext) -> TagEvidence:
    """
    Detect meaningless prophylaxis.

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
            tag="prophylactic_meaningless",
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

    eval_before_cp = ctx.eval_before_cp
    delta_eval = ctx.delta_eval
    drop_cp = int(delta_eval * 100)

    # Store evidence
    evidence.update({
        "preventive_score": preventive_score,
        "eval_before_cp": eval_before_cp,
        "delta_eval": delta_eval,
        "drop_cp": drop_cp,
    })
    evidence.update(preventive_data)

    # Gate 2: Some prophylactic intent (preventive score > 0)
    if preventive_score > 0.0:
        gates_passed.append("prophylactic_intent")
    else:
        gates_failed.append("prophylactic_intent")

    # Gate 3: In neutral evaluation band
    in_eval_band = abs(eval_before_cp) <= FAIL_EVAL_BAND_CP
    evidence["in_eval_band"] = in_eval_band

    if in_eval_band:
        gates_passed.append("neutral_eval_band")
    else:
        gates_failed.append("neutral_eval_band")

    # Gate 4: Significant evaluation loss
    eval_loss = drop_cp < -FAIL_DROP_CP
    evidence["eval_loss"] = eval_loss

    if eval_loss:
        gates_passed.append("eval_loss")
    else:
        gates_failed.append("eval_loss")

    # Fire if all gates pass
    fired = len(gates_passed) == 4

    # Compute confidence
    if fired:
        # Higher confidence for worse losses
        loss_magnitude = abs(drop_cp) - FAIL_DROP_CP
        loss_bonus = min(0.3, loss_magnitude / 100.0)
        intent_penalty = min(0.2, preventive_score * 0.5)
        confidence = 0.6 + loss_bonus + intent_penalty
    else:
        confidence = 0.0

    return TagEvidence(
        tag="prophylactic_meaningless",
        fired=fired,
        confidence=min(1.0, confidence),
        evidence=evidence,
        gates_passed=gates_passed,
        gates_failed=gates_failed,
    )


__all__ = ["detect"]
