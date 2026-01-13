"""
Maneuver detection helper functions.

Provides helper functions for detecting piece maneuvers - repositioning moves
that aim to improve piece placement, often involving knights and bishops.

Maneuvers are typically non-forcing moves that reposition pieces to better squares.
"""
import chess
from typing import Dict
from ...models import TagContext


def is_maneuver_candidate(ctx: TagContext) -> bool:
    """
    Check if move is a maneuver candidate.

    Maneuvers are typically:
    - Minor piece (N/B) moves
    - Not captures
    - Not checks
    - Quiet repositioning moves

    Args:
        ctx: Tag detection context

    Returns:
        True if move is a maneuver candidate
    """
    board = ctx.board
    move = ctx.played_move
    piece = board.piece_at(move.from_square)

    # Must be a minor piece move
    if not piece or piece.piece_type not in (chess.KNIGHT, chess.BISHOP):
        return False

    # Not a capture
    if board.is_capture(move):
        return False

    # Not a check
    board_after = board.copy()
    board_after.push(move)
    if board_after.is_check():
        return False

    # Quiet repositioning move
    return ctx.played_kind == "quiet"


def compute_maneuver_score(ctx: TagContext) -> Dict[str, float]:
    """
    Compute maneuver quality metrics.

    Scores:
    - maneuver: Overall quality based on metrics improvement
    - aggression: How aggressive/forcing the maneuver is
    - safety: Safety-oriented vs activity-oriented

    Args:
        ctx: Tag detection context

    Returns:
        Dict with maneuver scores
    """
    mobility_gain = ctx.component_deltas.get("mobility", 0.0)
    center_gain = ctx.component_deltas.get("center_control", 0.0)
    king_safety_gain = ctx.component_deltas.get("king_safety", 0.0)
    structure_change = ctx.component_deltas.get("structure", 0.0)
    eval_delta = ctx.delta_eval

    contact_delta = ctx.contact_ratio_played - ctx.contact_ratio_before

    # Maneuver quality score
    # Positive: improves mobility and center
    # Negative: loses evaluation
    maneuver_score = (
        0.5 * mobility_gain
        + 0.3 * center_gain
        - 0.2 * max(0.0, -eval_delta)
    )
    maneuver_score = max(-1.0, min(1.0, maneuver_score))

    # Aggression score (tension creation)
    structure_drop = max(0.0, -structure_change)
    aggression = max(0.0, min(1.0, contact_delta - structure_drop))

    # Safety bias (defensive vs offensive)
    safety_bias = max(-1.0, min(1.0, king_safety_gain - mobility_gain))

    return {
        "maneuver_score": round(maneuver_score, 3),
        "aggression": round(aggression, 3),
        "safety_bias": round(safety_bias, 3),
    }


__all__ = [
    "is_maneuver_candidate",
    "compute_maneuver_score",
]
