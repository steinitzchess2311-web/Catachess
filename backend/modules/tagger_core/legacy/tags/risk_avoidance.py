"""
Risk Avoidance tag detector.

Detects when a player trades mobility for king safety or opponent tactical
reduction, indicating a risk-averse move that prioritizes safety over activity.

Conditions:
- mobility_delta <= -0.05 (small mobility sacrifice)
- (king_safety_gain >= 0.05 OR opp_tactics_delta <= -0.05)
- delta_eval > -0.5 pawns (not too costly)

Evidence:
- mobility_delta: Change in mobility
- king_safety_gain: Improvement in king safety
- opp_tactics_delta: Reduction in opponent's tactical opportunities
- delta_eval: Evaluation cost
"""
from ...models import TagContext, TagEvidence


def detect(ctx: TagContext) -> TagEvidence:
    """
    Detect risk avoidance.

    Args:
        ctx: Tag detection context

    Returns:
        TagEvidence with detection result
    """
    gates_passed = []
    gates_failed = []
    evidence = {}

    # Thresholds
    mobility_sacrifice_threshold = -0.05
    king_safety_gain_threshold = 0.05
    opp_tactics_reduction_threshold = -0.05
    eval_cost_limit = -0.5

    # Get metric deltas
    mobility_delta = ctx.component_deltas.get("mobility", 0.0)
    king_safety_gain = ctx.component_deltas.get("king_safety", 0.0)
    opp_tactics_delta = ctx.opp_component_deltas.get("tactics", 0.0)
    delta_eval = ctx.delta_eval

    # Store evidence
    evidence["mobility_delta"] = mobility_delta
    evidence["king_safety_gain"] = king_safety_gain
    evidence["opp_tactics_delta"] = opp_tactics_delta
    evidence["delta_eval"] = delta_eval
    evidence["eval_cost_cp"] = int(delta_eval * 100)

    # Gate 1: Mobility sacrifice
    if mobility_delta <= mobility_sacrifice_threshold:
        gates_passed.append("mobility_sacrifice")
    else:
        gates_failed.append("mobility_sacrifice")

    # Gate 2: Gained king safety OR reduced opponent tactics
    safety_or_tactics = False
    if king_safety_gain >= king_safety_gain_threshold:
        gates_passed.append("king_safety_improvement")
        safety_or_tactics = True
    else:
        gates_failed.append("king_safety_improvement")

    if opp_tactics_delta <= opp_tactics_reduction_threshold:
        gates_passed.append("opponent_tactics_reduction")
        safety_or_tactics = True
    else:
        gates_failed.append("opponent_tactics_reduction")

    # Gate 3: Not too costly in evaluation
    if delta_eval > eval_cost_limit:
        gates_passed.append("acceptable_eval_cost")
    else:
        gates_failed.append("acceptable_eval_cost")

    # Fire if: mobility sacrifice + (safety OR tactics) + acceptable cost
    fired = (
        "mobility_sacrifice" in gates_passed
        and safety_or_tactics
        and "acceptable_eval_cost" in gates_passed
    )

    # Compute confidence
    if fired:
        # Higher confidence for better safety/tactics tradeoffs
        safety_bonus = min(0.3, king_safety_gain * 3.0)
        tactics_bonus = min(0.3, abs(opp_tactics_delta) * 3.0)
        cost_bonus = min(0.2, (delta_eval - eval_cost_limit) * 0.3)
        confidence = 0.4 + safety_bonus + tactics_bonus + cost_bonus
    else:
        confidence = 0.0

    return TagEvidence(
        tag="risk_avoidance",
        fired=fired,
        confidence=min(1.0, confidence),
        evidence=evidence,
        gates_passed=gates_passed,
        gates_failed=gates_failed,
    )


__all__ = ["detect"]
