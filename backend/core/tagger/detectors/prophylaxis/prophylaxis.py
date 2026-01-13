"""
Prophylaxis tag detectors - 5 detectors using rule_tagger2 logic.

Updated in Stage 4 to use:
- classify_prophylaxis_quality() for precise classification
- is_prophylaxis_candidate() for candidate filtering
- compute_preventive_score() for preventive score calculation

Matches rule_tagger2/legacy/prophylaxis.py and core.py exactly.
"""
from ...models import TagContext, TagEvidence
from ...detectors.helpers.prophylaxis import (
    classify_prophylaxis_quality,
    compute_preventive_score,
    compute_soft_weight,
    is_prophylaxis_candidate,
    prophylaxis_pattern_reason,
    ProphylaxisConfig,
)


def detect_prophylactic_move(ctx: TagContext) -> TagEvidence:
    """
    General prophylactic move detection.

    Uses is_prophylaxis_candidate() gate and compute_preventive_score().
    Fires if preventive_score >= config.preventive_trigger.
    """
    gates_passed, gates_failed, evidence = [], [], {}
    config = ProphylaxisConfig()

    # Gate 1: Candidate filtering
    if not is_prophylaxis_candidate(ctx.board_before, ctx.played_move):
        gates_failed.append("candidate")
        evidence.update({"reason": "not a prophylaxis candidate (capture, check, early opening, etc.)"})
        return TagEvidence("prophylactic_move", False, 0.0, evidence, gates_passed, gates_failed)

    gates_passed.append("candidate")

    # Compute preventive score
    preventive_score = compute_preventive_score(ctx, config)
    evidence.update({
        "preventive_score": preventive_score,
        "trigger": config.preventive_trigger,
    })

    # Gate 2: Score threshold
    if preventive_score >= config.preventive_trigger:
        gates_passed.append("score_threshold")
        fired = True
        # Confidence scales with score: 0.16 -> 0.65, 0.6 -> 1.0
        confidence = min(1.0, 0.5 + preventive_score * 0.8)
    else:
        gates_failed.append("score_threshold")
        fired = False
        confidence = 0.0

    return TagEvidence("prophylactic_move", fired, confidence, evidence, gates_passed, gates_failed)


def detect_prophylactic_direct(ctx: TagContext) -> TagEvidence:
    """
    High-quality direct prophylaxis detection.

    Uses classify_prophylaxis_quality() from rule_tagger2.
    Fires when label == "prophylactic_direct".
    """
    gates_passed, gates_failed, evidence = [], [], {}
    config = ProphylaxisConfig()

    # Gate 1: Candidate filtering
    if not is_prophylaxis_candidate(ctx.board_before, ctx.played_move):
        gates_failed.append("candidate")
        return TagEvidence("prophylactic_direct", False, 0.0, evidence, gates_passed, gates_failed)

    gates_passed.append("candidate")

    # Compute inputs for classification
    preventive_score = compute_preventive_score(ctx, config)
    soft_weight = compute_soft_weight(ctx)

    # Extract context parameters (with safe defaults)
    effective_delta = getattr(ctx, "effective_delta", ctx.delta_eval)
    tactical_weight = getattr(ctx, "tactical_weight", 0.5)
    eval_before_cp = int(getattr(ctx, "eval_before_cp", getattr(ctx, "eval_before", 0.0) * 100))
    drop_cp = int(ctx.delta_eval * 100)
    threat_delta = getattr(ctx, "threat_delta", 0.0)
    volatility_drop = getattr(ctx, "volatility_drop", 0.0)

    # Check for pattern support
    opp_trend = ctx.opp_component_deltas.get("mobility", 0.0) + ctx.opp_component_deltas.get("tactics", 0.0)
    pattern_support = prophylaxis_pattern_reason(
        ctx.board_before,
        ctx.played_move,
        opp_trend,
        ctx.opp_component_deltas.get("tactics", 0.0)
    )
    pattern_override = pattern_support is not None

    # Classify quality using rule_tagger2 logic
    label, confidence = classify_prophylaxis_quality(
        has_prophylaxis=True,
        preventive_score=preventive_score,
        effective_delta=effective_delta,
        tactical_weight=tactical_weight,
        soft_weight=soft_weight,
        eval_before_cp=eval_before_cp,
        drop_cp=drop_cp,
        threat_delta=threat_delta,
        volatility_drop=volatility_drop,
        pattern_override=pattern_override,
        config=config,
    )

    evidence.update({
        "preventive_score": preventive_score,
        "soft_weight": soft_weight,
        "classification": label,
        "confidence": confidence,
        "pattern_support": pattern_support,
    })

    # Fire only if classified as "prophylactic_direct"
    if label == "prophylactic_direct":
        gates_passed.append("direct_classification")
        fired = True
    else:
        gates_failed.append("direct_classification")
        fired = False
        confidence = 0.0

    return TagEvidence("prophylactic_direct", fired, confidence, evidence, gates_passed, gates_failed)


def detect_prophylactic_latent(ctx: TagContext) -> TagEvidence:
    """
    Subtle/latent prophylaxis detection.

    Uses classify_prophylaxis_quality() from rule_tagger2.
    Fires when label == "prophylactic_latent".
    """
    gates_passed, gates_failed, evidence = [], [], {}
    config = ProphylaxisConfig()

    # Gate 1: Candidate filtering
    if not is_prophylaxis_candidate(ctx.board_before, ctx.played_move):
        gates_failed.append("candidate")
        return TagEvidence("prophylactic_latent", False, 0.0, evidence, gates_passed, gates_failed)

    gates_passed.append("candidate")

    # Compute inputs for classification
    preventive_score = compute_preventive_score(ctx, config)
    soft_weight = compute_soft_weight(ctx)

    # Extract context parameters
    effective_delta = getattr(ctx, "effective_delta", ctx.delta_eval)
    tactical_weight = getattr(ctx, "tactical_weight", 0.5)
    eval_before_cp = int(getattr(ctx, "eval_before_cp", getattr(ctx, "eval_before", 0.0) * 100))
    drop_cp = int(ctx.delta_eval * 100)
    threat_delta = getattr(ctx, "threat_delta", 0.0)
    volatility_drop = getattr(ctx, "volatility_drop", 0.0)

    # Check for pattern support
    opp_trend = ctx.opp_component_deltas.get("mobility", 0.0) + ctx.opp_component_deltas.get("tactics", 0.0)
    pattern_support = prophylaxis_pattern_reason(
        ctx.board_before,
        ctx.played_move,
        opp_trend,
        ctx.opp_component_deltas.get("tactics", 0.0)
    )
    pattern_override = pattern_support is not None

    # Classify quality
    label, confidence = classify_prophylaxis_quality(
        has_prophylaxis=True,
        preventive_score=preventive_score,
        effective_delta=effective_delta,
        tactical_weight=tactical_weight,
        soft_weight=soft_weight,
        eval_before_cp=eval_before_cp,
        drop_cp=drop_cp,
        threat_delta=threat_delta,
        volatility_drop=volatility_drop,
        pattern_override=pattern_override,
        config=config,
    )

    evidence.update({
        "preventive_score": preventive_score,
        "soft_weight": soft_weight,
        "classification": label,
        "confidence": confidence,
        "pattern_support": pattern_support,
    })

    # Fire only if classified as "prophylactic_latent"
    if label == "prophylactic_latent":
        gates_passed.append("latent_classification")
        fired = True
    else:
        gates_failed.append("latent_classification")
        fired = False
        confidence = 0.0

    return TagEvidence("prophylactic_latent", fired, confidence, evidence, gates_passed, gates_failed)


def detect_prophylactic_meaningless(ctx: TagContext) -> TagEvidence:
    """
    Meaningless/failed prophylaxis detection.

    Uses classify_prophylaxis_quality() from rule_tagger2.
    Fires when label == "prophylactic_meaningless".
    """
    gates_passed, gates_failed, evidence = [], [], {}
    config = ProphylaxisConfig()

    # Gate 1: Candidate filtering
    if not is_prophylaxis_candidate(ctx.board_before, ctx.played_move):
        gates_failed.append("candidate")
        return TagEvidence("prophylactic_meaningless", False, 0.0, evidence, gates_passed, gates_failed)

    gates_passed.append("candidate")

    # Compute inputs for classification
    preventive_score = compute_preventive_score(ctx, config)
    soft_weight = compute_soft_weight(ctx)

    # Extract context parameters
    effective_delta = getattr(ctx, "effective_delta", ctx.delta_eval)
    tactical_weight = getattr(ctx, "tactical_weight", 0.5)
    eval_before_cp = int(getattr(ctx, "eval_before_cp", getattr(ctx, "eval_before", 0.0) * 100))
    drop_cp = int(ctx.delta_eval * 100)
    threat_delta = getattr(ctx, "threat_delta", 0.0)
    volatility_drop = getattr(ctx, "volatility_drop", 0.0)

    # Check for pattern support
    opp_trend = ctx.opp_component_deltas.get("mobility", 0.0) + ctx.opp_component_deltas.get("tactics", 0.0)
    pattern_support = prophylaxis_pattern_reason(
        ctx.board_before,
        ctx.played_move,
        opp_trend,
        ctx.opp_component_deltas.get("tactics", 0.0)
    )
    pattern_override = pattern_support is not None

    # Classify quality
    label, confidence = classify_prophylaxis_quality(
        has_prophylaxis=True,
        preventive_score=preventive_score,
        effective_delta=effective_delta,
        tactical_weight=tactical_weight,
        soft_weight=soft_weight,
        eval_before_cp=eval_before_cp,
        drop_cp=drop_cp,
        threat_delta=threat_delta,
        volatility_drop=volatility_drop,
        pattern_override=pattern_override,
        config=config,
    )

    evidence.update({
        "preventive_score": preventive_score,
        "soft_weight": soft_weight,
        "classification": label,
        "confidence": confidence,
        "pattern_support": pattern_support,
        "eval_drop": drop_cp,
    })

    # Fire only if classified as "prophylactic_meaningless"
    if label == "prophylactic_meaningless":
        gates_passed.append("meaningless_classification")
        fired = True
    else:
        gates_failed.append("meaningless_classification")
        fired = False
        confidence = 0.0

    return TagEvidence("prophylactic_meaningless", fired, confidence, evidence, gates_passed, gates_failed)


def detect_failed_prophylactic(ctx: TagContext) -> TagEvidence:
    """
    Failed prophylaxis (alias for meaningless).

    This is a legacy detector that maps to prophylactic_meaningless.
    Kept for backward compatibility.
    """
    # Reuse meaningless detection logic
    result = detect_prophylactic_meaningless(ctx)

    # Change tag name to maintain backward compatibility
    return TagEvidence(
        "failed_prophylactic",
        result.fired,
        result.confidence,
        result.evidence,
        result.gates_passed,
        result.gates_failed
    )


__all__ = [
    "detect_prophylactic_move",
    "detect_prophylactic_direct",
    "detect_prophylactic_latent",
    "detect_prophylactic_meaningless",
    "detect_failed_prophylactic",
]
