"""
Subtype detection for CoD v2.
Each function detects one specific subtype.
"""
from .models import CoDContext
from .result import CoDResult, CoDSubtype
from .thresholds import CoDThresholds


def detect_prophylaxis(
    ctx: CoDContext,
    thresholds: CoDThresholds,
) -> CoDResult:
    """
    Detect prophylaxis subtype.
    Prevents opponent plans through preventive moves.
    """
    m = ctx.metrics

    # Check preventive score
    if m.preventive_score < thresholds.preventive_trigger:
        return CoDResult.no_detection()

    # Check threat delta
    if m.threat_delta < thresholds.threat_drop_min:
        return CoDResult.no_detection()

    # Check mobility drop
    if m.opp_mobility_drop < thresholds.opp_mobility_drop:
        return CoDResult.no_detection()

    confidence = min(1.0, m.preventive_score)

    return CoDResult(
        detected=True,
        subtype=CoDSubtype.PROPHYLAXIS,
        confidence=confidence,
        evidence={
            "preventive_score": m.preventive_score,
            "threat_delta": m.threat_delta,
            "opp_mobility_drop": m.opp_mobility_drop,
        },
        thresholds_used=thresholds.to_dict(),
    )


def detect_piece_control(
    ctx: CoDContext,
    thresholds: CoDThresholds,
) -> CoDResult:
    """
    Detect piece control subtype.
    Restricts opponent mobility via piece activity.
    """
    m = ctx.metrics

    # Check mobility drop
    if m.opp_mobility_drop < thresholds.opp_mobility_drop:
        return CoDResult.no_detection()

    # Check volatility drop
    if m.volatility_drop_cp < thresholds.volatility_drop_cp:
        return CoDResult.no_detection()

    # Piece control requires positive self mobility or neutral
    if m.self_mobility_change < -0.1:
        return CoDResult.no_detection()

    confidence = min(1.0, m.opp_mobility_drop / thresholds.opp_mobility_drop)

    return CoDResult(
        detected=True,
        subtype=CoDSubtype.PIECE_CONTROL,
        confidence=confidence,
        evidence={
            "opp_mobility_drop": m.opp_mobility_drop,
            "volatility_drop_cp": m.volatility_drop_cp,
            "self_mobility_change": m.self_mobility_change,
        },
        thresholds_used=thresholds.to_dict(),
    )


def detect_pawn_control(
    ctx: CoDContext,
    thresholds: CoDThresholds,
) -> CoDResult:
    """
    Detect pawn control subtype.
    Restricts opponent mobility via pawn structure.
    """
    m = ctx.metrics

    # Must establish blockade or reduce passed pawn threats
    if not m.blockade_established and m.opp_passed_push_drop < 0.1:
        return CoDResult.no_detection()

    # Check mobility/structure metrics
    if m.opp_mobility_drop < 0.1 and m.structure_gain < 0.15:
        return CoDResult.no_detection()

    confidence = 0.7  # Base confidence for pawn control

    return CoDResult(
        detected=True,
        subtype=CoDSubtype.PAWN_CONTROL,
        confidence=confidence,
        evidence={
            "blockade_established": m.blockade_established,
            "opp_passed_push_drop": m.opp_passed_push_drop,
            "structure_gain": m.structure_gain,
        },
        thresholds_used=thresholds.to_dict(),
    )


def detect_simplification(
    ctx: CoDContext,
    thresholds: CoDThresholds,
) -> CoDResult:
    """
    Detect simplification subtype.
    Reduces complexity via exchanges.
    """
    m = ctx.metrics

    # Check exchange count
    if m.exchange_count < 1:
        return CoDResult.no_detection()

    # Check total piece reduction
    if m.total_active_drop < thresholds.simplify_min_exchange:
        return CoDResult.no_detection()

    # Simplification requires evaluation not dropping significantly
    if ctx.eval_drop_cp < -50:
        return CoDResult.no_detection()

    confidence = min(1.0, m.total_active_drop / thresholds.simplify_min_exchange)

    return CoDResult(
        detected=True,
        subtype=CoDSubtype.SIMPLIFICATION,
        confidence=confidence,
        evidence={
            "exchange_count": m.exchange_count,
            "total_active_drop": m.total_active_drop,
            "eval_drop_cp": ctx.eval_drop_cp,
        },
        thresholds_used=thresholds.to_dict(),
    )


__all__ = [
    "detect_prophylaxis",
    "detect_piece_control",
    "detect_pawn_control",
    "detect_simplification",
]
