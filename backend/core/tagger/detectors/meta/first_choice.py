"""
First Choice tag detector.
Fires when the played move is the engine's top choice.
"""
from core.tagger.models import TagContext, TagEvidence
from ...config import TACTICAL_GAP_FIRST_CHOICE


def detect(ctx: TagContext) -> TagEvidence:
    """
    Detect if played move is the first choice.

    Args:
        ctx: Tag context with analysis data

    Returns:
        TagEvidence for first_choice tag
    """
    gates_passed = []
    gates_failed = []
    evidence = {}

    # Check if played move matches best move
    is_best_move = ctx.played_move == ctx.best_move

    if is_best_move:
        gates_passed.append("played_is_best")
        evidence["played_move"] = ctx.played_move.uci()
        evidence["best_move"] = ctx.best_move.uci()
        evidence["eval_delta"] = ctx.delta_eval
        fired = True
        confidence = 1.0
    else:
        gates_failed.append("played_is_best")
        # Check if move is within tactical gap threshold
        if abs(ctx.delta_eval) <= TACTICAL_GAP_FIRST_CHOICE / 100.0:
            gates_passed.append("within_tactical_gap")
            evidence["eval_delta"] = ctx.delta_eval
            evidence["threshold"] = TACTICAL_GAP_FIRST_CHOICE / 100.0
            fired = True
            confidence = 0.8  # Lower confidence when not exact best
        else:
            gates_failed.append("within_tactical_gap")
            evidence["eval_delta"] = ctx.delta_eval
            evidence["threshold"] = TACTICAL_GAP_FIRST_CHOICE / 100.0
            fired = False
            confidence = 0.0

    return TagEvidence(
        tag="first_choice",
        fired=fired,
        confidence=confidence,
        evidence=evidence,
        gates_passed=gates_passed,
        gates_failed=gates_failed,
    )


__all__ = ["detect"]
