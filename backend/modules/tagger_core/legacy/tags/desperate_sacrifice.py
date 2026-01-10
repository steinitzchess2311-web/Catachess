"""
Desperate Sacrifice tag detector.

Detects desperate sacrifices - material sacrificed from a losing position
as a last-ditch attempt to create complications or counterplay.

Conditions:
- Move is a sacrifice (material loss ≥ 0.5 pawns)
- Position before move is losing (eval ≤ -3.0 pawns)

This tag can co-fire with other sacrifice tags (tactical, positional, etc.)
to indicate the context was desperate. Desperate sacrifices may be the
objectively best try in bad positions.

Evidence:
- is_sacrifice: Whether move sacrifices material
- material_delta: Material loss in pawns
- eval_before: Evaluation before move (losing)
- desperate_context: Whether position is losing
"""
from ...models import TagContext, TagEvidence
from ..shared.sacrifice_helpers import is_sacrifice_candidate


# Threshold for "desperate" position (3 pawns down)
DESPERATE_EVAL_THRESHOLD = -3.0


def detect(ctx: TagContext) -> TagEvidence:
    """
    Detect desperate sacrifice.

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
            tag="desperate_sacrifice",
            fired=False,
            confidence=0.0,
            evidence=evidence,
            gates_passed=gates_passed,
            gates_failed=gates_failed,
        )

    # Check eval before move
    eval_before = ctx.eval_before

    # Store evidence
    evidence["eval_before"] = eval_before
    evidence["desperate_threshold"] = DESPERATE_EVAL_THRESHOLD

    # Gate 2: Losing position (desperate context)
    desperate_context = eval_before <= DESPERATE_EVAL_THRESHOLD
    evidence["desperate_context"] = desperate_context

    if desperate_context:
        gates_passed.append("desperate_context")
    else:
        gates_failed.append("desperate_context")

    # Fire if both gates pass
    fired = len(gates_passed) == 2

    # Compute confidence
    if fired:
        # Higher confidence for worse starting positions
        desperation_magnitude = abs(eval_before - DESPERATE_EVAL_THRESHOLD)
        desperation_bonus = min(0.3, desperation_magnitude * 0.1)
        confidence = 0.7 + desperation_bonus
    else:
        confidence = 0.0

    return TagEvidence(
        tag="desperate_sacrifice",
        fired=fired,
        confidence=min(1.0, confidence),
        evidence=evidence,
        gates_passed=gates_passed,
        gates_failed=gates_failed,
    )


__all__ = ["detect"]
