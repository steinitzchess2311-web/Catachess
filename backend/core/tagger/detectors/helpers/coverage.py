"""
Coverage computation for attack and defense metrics.
Measures piece activity through square control and mobility.
"""
import chess
from typing import Dict, Set


def compute_coverage(board: chess.Board, color: chess.Color) -> int:
    """
    Compute coverage score for a given side.

    Coverage = sum of attacked squares weighted by piece value.

    Args:
        board: Chess board
        color: Color to compute coverage for

    Returns:
        Coverage score (0-100 range typically)
    """
    attacked_squares = get_attacked_squares(board, color)
    coverage = len(attacked_squares)

    # Weight by piece importance
    for square in attacked_squares:
        piece = board.piece_at(square)
        if piece and piece.color != color:
            # Attacking opponent pieces
            coverage += _piece_weight(piece.piece_type)

    return coverage


def compute_coverage_delta(
    board_before: chess.Board,
    board_after: chess.Board,
    color: chess.Color,
) -> int:
    """
    Compute change in coverage before and after a move.

    Args:
        board_before: Board before move
        board_after: Board after move
        color: Color that made the move

    Returns:
        Coverage delta (positive = improvement)
    """
    coverage_before = compute_coverage(board_before, color)
    coverage_after = compute_coverage(board_after, color)
    return coverage_after - coverage_before


def get_attacked_squares(board: chess.Board, color: chess.Color) -> Set[int]:
    """
    Get all squares attacked by a given side.

    Args:
        board: Chess board
        color: Color to get attacks for

    Returns:
        Set of square indices
    """
    attacked = set()

    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece and piece.color == color:
            attacked.update(board.attacks(square))

    return attacked


def _piece_weight(piece_type: chess.PieceType) -> int:
    """Get weight for piece type in coverage calculation."""
    weights = {
        chess.PAWN: 1,
        chess.KNIGHT: 3,
        chess.BISHOP: 3,
        chess.ROOK: 5,
        chess.QUEEN: 9,
        chess.KING: 0,  # King defense doesn't count as attack
    }
    return weights.get(piece_type, 0)


__all__ = [
    "compute_coverage",
    "compute_coverage_delta",
    "get_attacked_squares",
]
