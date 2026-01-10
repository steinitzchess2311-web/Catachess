"""
Positional Structure Sacrifice tag detector.

Detects positional sacrifices made for structural or king safety advantages -
material sacrificed to improve pawn structure, piece placement, or king safety.

Conditions:
- Move is a positional sacrifice (sound non-tactical sacrifice)
- Strong structure signal:
  - Structure component gains significantly (≥ 0.15), OR
  - King safety gains significantly (≥ 0.1)

This is a subtype of positional_sacrifice that emphasizes long-term
structural improvements over dynamic factors.

Evidence:
- is_positional_sacrifice: Whether positional_sacrifice fires
- structure_gain: Structure component delta
- king_gain: King safety delta
- structure_signal: Whether structure criteria met
"""
from ...models import TagContext, TagEvidence
from . import positional_sacrifice


# Thresholds
STRUCTURE_GAIN_THRESHOLD = 0.15
KING_GAIN_THRESHOLD = 0.1


def detect(ctx: TagContext) -> TagEvidence:
    """
    Detect positional structure sacrifice.

    Args:
        ctx: Tag detection context

    Returns:
        TagEvidence with detection result
    """
    gates_passed = []
    gates_failed = []
    evidence = {}

    # Check if positional_sacrifice fires
    positional_sac_evidence = positional_sacrifice.detect(ctx)
    is_positional_sac = positional_sac_evidence.fired

    evidence["is_positional_sacrifice"] = is_positional_sac

    # Gate 1: Must be positional sacrifice
    if is_positional_sac:
        gates_passed.append("is_positional_sacrifice")
    else:
        gates_failed.append("is_positional_sacrifice")
        return TagEvidence(
            tag="positional_structure_sacrifice",
            fired=False,
            confidence=0.0,
            evidence=evidence,
            gates_passed=gates_passed,
            gates_failed=gates_failed,
        )

    # Check structure signals
    structure_gain = ctx.component_deltas.get("structure", 0.0)
    king_gain = ctx.component_deltas.get("king_safety", 0.0)

    evidence["structure_gain"] = structure_gain
    evidence["king_gain"] = king_gain

    # Gate 2: Structure signal
    structure_signal = (
        structure_gain >= STRUCTURE_GAIN_THRESHOLD
        or king_gain >= KING_GAIN_THRESHOLD
    )
    evidence["structure_signal"] = structure_signal

    if structure_signal:
        gates_passed.append("structure_signal")
    else:
        gates_failed.append("structure_signal")

    # Fire if both gates pass
    fired = len(gates_passed) == 2

    # Compute confidence
    if fired:
        # Higher confidence for stronger structural gains
        base = positional_sac_evidence.confidence * 0.7
        structure_bonus = min(0.15, max(0.0, structure_gain - STRUCTURE_GAIN_THRESHOLD) * 0.6)
        king_bonus = min(0.15, max(0.0, king_gain - KING_GAIN_THRESHOLD) * 0.8)
        confidence = base + structure_bonus + king_bonus
    else:
        confidence = 0.0

    return TagEvidence(
        tag="positional_structure_sacrifice",
        fired=fired,
        confidence=min(1.0, confidence),
        evidence=evidence,
        gates_passed=gates_passed,
        gates_failed=gates_failed,
    )


__all__ = ["detect"]
