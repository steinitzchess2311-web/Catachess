"""
Prophylaxis detection helpers.

This module provides helper functions for detecting prophylactic moves -
anticipatory moves that prevent opponent threats or restrict opponent play.

Key concepts:
- Prophylaxis is anticipatory, not reactive (no captures, checks, or responses to check)
- Preventive score: measures opponent restriction (mobility drop, tactics drop, threat reduction)
- Soft weight: measures positional consolidation (structure, king safety)
- Pattern support: canonical prophylaxis motifs (bishop retreat, knight reposition, etc.)

Functions:
- is_prophylaxis_candidate(): Gate to check eligibility
- compute_preventive_score(): Compute opponent restriction score
- compute_soft_weight(): Compute positional consolidation score
- prophylaxis_pattern_reason(): Detect canonical motifs
- is_full_material(): Check if all 32 pieces remain
"""
from typing import Optional, Dict, Any
import chess
from ...models import TagContext

# Thresholds
FULL_MATERIAL_COUNT = 32
OPENING_MOVE_CUTOFF = 6  # Only block prophylaxis if fullmove < 6 AND all pieces present
STRUCTURE_MIN = 0.2
OPP_MOBILITY_DROP = 0.15
SELF_MOBILITY_TOL = 0.3
PREVENTIVE_TRIGGER = 0.16
SAFETY_CAP = 0.6
SCORE_THRESHOLD = 0.20
THREAT_DROP = 0.35


def is_full_material(board: chess.Board) -> bool:
    """Return True when all 32 pieces remain on the board."""
    return len(board.piece_map()) >= FULL_MATERIAL_COUNT


def is_prophylaxis_candidate(ctx: TagContext) -> bool:
    """
    Heuristic gate to decide whether a move is eligible for prophylaxis tagging.

    Prophylactic moves must be anticipatory, not reactive. This excludes:
    - Full material positions in early opening (opening noise)
    - Moves that give check (too aggressive)
    - Captures (tactical, not prophylactic)
    - Moves while in check (reactive)
    - Recaptures (reactive)
    - Very early opening moves (prophylaxis is middlegame/endgame concept)

    Args:
        ctx: Tag detection context

    Returns:
        True if move is eligible for prophylaxis tagging
    """
    board = ctx.board
    move = ctx.played_move

    # Exclude full material opening phase
    if is_full_material(board) and board.fullmove_number < OPENING_MOVE_CUTOFF:
        return False

    # Exclude forcing moves (checks)
    if board.gives_check(move):
        return False

    # Get piece being moved
    piece = board.piece_at(move.from_square)
    if not piece:
        return False

    # Exclude captures - tactical, not prophylactic
    if board.is_capture(move):
        return False

    # Exclude moves while in check - reactive, not anticipatory
    if board.is_check():
        return False

    # Exclude recaptures: if opponent just moved to destination square
    if len(board.move_stack) > 0:
        last_move = board.peek()
        if last_move.to_square == move.to_square:
            return False

    return True


def compute_preventive_score(ctx: TagContext) -> Dict[str, Any]:
    """
    Compute preventive score based on opponent restriction.

    Preventive score measures how much the move restricts opponent's resources:
    - Opponent mobility drop (weight 0.3)
    - Opponent tactics drop (weight 0.2)
    - Opponent trend (weight 0.15)

    Note: threat_delta (weight 0.5) is omitted here as it requires engine analysis
    not available in TagContext. For full prophylaxis detection, integrate with
    engine-based threat estimation.

    Args:
        ctx: Tag detection context

    Returns:
        Dict with preventive_score and component breakdowns
    """
    opp_mobility_delta = ctx.opp_component_deltas.get("mobility", 0.0)
    opp_tactics_delta = ctx.opp_component_deltas.get("tactics", 0.0)

    # Compute opponent trend (simplified: just mobility + tactics)
    opp_trend = opp_mobility_delta + opp_tactics_delta

    # Preventive score: reward opponent restriction
    preventive_score = (
        max(0.0, -opp_mobility_delta) * 0.3
        + max(0.0, -opp_tactics_delta) * 0.2
        + max(0.0, -opp_trend) * 0.15
    )

    return {
        "preventive_score": round(preventive_score, 3),
        "opp_mobility_delta": round(opp_mobility_delta, 3),
        "opp_tactics_delta": round(opp_tactics_delta, 3),
        "opp_trend": round(opp_trend, 3),
        "opp_restrained": (
            opp_trend < 0.0
            or opp_mobility_delta <= -0.05
            or opp_tactics_delta <= -0.1
        ),
    }


def compute_soft_weight(ctx: TagContext) -> float:
    """
    Compute soft positioning weight based on self-consolidation.

    Soft weight measures positional improvements:
    - Structure gain (weight 0.4)
    - King safety gain (weight 0.4)
    - Controlled mobility drop (weight 0.2, reward slight drop as consolidation)

    Args:
        ctx: Tag detection context

    Returns:
        Soft weight score (0.0 to SAFETY_CAP)
    """
    structure_delta = ctx.component_deltas.get("structure", 0.0)
    king_safety_delta = ctx.component_deltas.get("king_safety", 0.0)
    mobility_delta = ctx.component_deltas.get("mobility", 0.0)

    # Reward structure and king safety gains
    # Reward controlled mobility drop (consolidation)
    soft_raw = (
        max(0.0, structure_delta) * 0.4
        + max(0.0, king_safety_delta) * 0.4
        + max(0.0, -mobility_delta) * 0.2
    )

    return round(min(soft_raw, SAFETY_CAP), 3)


__all__ = [
    "is_prophylaxis_candidate",
    "compute_preventive_score",
    "compute_soft_weight",
    "is_full_material",
    "STRUCTURE_MIN",
    "OPP_MOBILITY_DROP",
    "SELF_MOBILITY_TOL",
    "PREVENTIVE_TRIGGER",
    "SAFETY_CAP",
    "SCORE_THRESHOLD",
    "THREAT_DROP",
]
