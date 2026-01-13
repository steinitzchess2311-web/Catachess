"""
Control over Dynamics (CoD) helper functions.

Provides control metrics computation and gating functions used by CoD detectors.
These functions measure position control, tension, mobility restrictions, and
volatility changes that indicate control-oriented play.

Note: This is a simplified version extracting only the essential functions
from the legacy control_helpers.py (which is 400+ lines). More functions
can be added as needed when implementing specific CoD subtypes.
"""
from typing import Dict, Any, Optional
import chess
from .contact import contact_profile
from .phase import get_phase_bucket
from ...config.engine import (
    CONTROL_PHASE_WEIGHTS,
    CONTROL_TENSION_DELTA,
    CONTROL_TENSION_DELTA_ENDGAME,
)


def contact_stats(board: chess.Board, color: chess.Color) -> Dict[str, float]:
    """
    Get contact statistics for a specific color.

    Args:
        board: Chess board position
        color: Color to analyze

    Returns:
        Dict with keys: ratio, total, contact, captures, checks
    """
    probe = board.copy(stack=False)
    probe.turn = color
    ratio, total, capture_moves, checking_moves = contact_profile(probe)
    contact_total = capture_moves + checking_moves

    return {
        "ratio": ratio,
        "total": total,
        "contact": contact_total,
        "captures": capture_moves,
        "checks": checking_moves,
    }


def control_tension_threshold(phase_bucket: str) -> float:
    """
    Get phase-dependent tension threshold for CoD detection.

    Args:
        phase_bucket: Phase bucket ("opening", "middlegame", "endgame")

    Returns:
        Tension threshold (negative value, more negative = stricter)
    """
    weight = CONTROL_PHASE_WEIGHTS.get(phase_bucket, 1.0)
    base = CONTROL_TENSION_DELTA * weight

    if phase_bucket == "endgame":
        base = min(base, CONTROL_TENSION_DELTA_ENDGAME)

    return base


def count_legal_moves_for(board: chess.Board, color: chess.Color) -> int:
    """
    Count legal moves for a specific color.

    Args:
        board: Chess board position
        color: Color to count moves for

    Returns:
        Number of legal moves
    """
    probe = board.copy(stack=False)
    probe.turn = color
    return probe.legal_moves.count()


def active_piece_count(board: chess.Board) -> int:
    """
    Count active pieces (non-pawns, non-kings) for both sides.

    Args:
        board: Chess board position

    Returns:
        Total count of active pieces
    """
    return sum(
        1
        for piece in board.piece_map().values()
        if piece.piece_type not in (chess.KING, chess.PAWN)
    )


def active_piece_count_for(board: chess.Board, color: chess.Color) -> int:
    """
    Count active pieces for a specific color.

    Args:
        board: Chess board position
        color: Color to count for

    Returns:
        Count of active pieces (knights, bishops, rooks, queens)
    """
    total = 0
    for square in chess.SquareSet(board.occupied_co[color]):
        piece = board.piece_at(square)
        if piece and piece.piece_type not in (chess.KING, chess.PAWN):
            total += 1
    return total


def collect_control_metrics(
    board: chess.Board,
    played_board: chess.Board,
    actor: chess.Color,
    phase_ratio: float,
    analysis_meta: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Collect control-related metrics for CoD detection.

    This is a simplified version that computes the essential control metrics.
    Full implementation would include more fields (see legacy control_helpers.py).

    Args:
        board: Position before the move
        played_board: Position after the move
        actor: Color that played the move
        phase_ratio: Game phase ratio
        analysis_meta: Analysis metadata with volatility info

    Returns:
        Dict with control metrics:
        - tension_delta: Change in total contact moves
        - opp_mobility_drop: Decrease in opponent's mobility
        - volatility_drop_cp: Decrease in position volatility
        - phase: Phase bucket
    """
    phase_name = get_phase_bucket(phase_ratio)

    # Volatility calculation
    volatility_before_cp = abs(analysis_meta.get("depth_jump_cp", 0)) + abs(
        analysis_meta.get("deepening_gain_cp", 0)
    )
    volatility_after_cp = analysis_meta.get("control_volatility_after_cp", 0)
    volatility_drop_cp = max(0.0, volatility_before_cp - volatility_after_cp)

    # Contact/tension metrics
    self_contact_before = contact_stats(board, actor)
    opp_contact_before = contact_stats(board, not actor)
    self_contact_after = contact_stats(played_board, actor)
    opp_contact_after = contact_stats(played_board, not actor)

    tension_before = self_contact_before["contact"] + opp_contact_before["contact"]
    tension_after = self_contact_after["contact"] + opp_contact_after["contact"]
    tension_delta = tension_after - tension_before

    # Mobility metrics
    opp_mobility_before = count_legal_moves_for(board, not actor)
    opp_mobility_after = count_legal_moves_for(played_board, not actor)
    opp_mobility_drop = opp_mobility_before - opp_mobility_after

    return {
        "phase": phase_name,
        "tension_delta": tension_delta,
        "opp_mobility_drop": opp_mobility_drop,
        "volatility_drop_cp": volatility_drop_cp,
        "tension_before": tension_before,
        "tension_after": tension_after,
    }


__all__ = [
    "contact_stats",
    "control_tension_threshold",
    "count_legal_moves_for",
    "active_piece_count",
    "active_piece_count_for",
    "collect_control_metrics",
]
