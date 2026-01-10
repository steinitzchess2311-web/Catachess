"""
Contact ratio computation for chess positions.

Contact ratio measures the proportion of moves that are "contact" moves
(captures or checks) out of all legal moves. Higher ratios indicate more
tactical/forcing positions.
"""
from typing import Tuple
import chess


def contact_profile(board: chess.Board) -> Tuple[float, int, int, int]:
    """
    Compute contact ratio for a position.

    Contact moves are captures or checks. This ratio helps identify tactical
    positions and is used in tension detection, tactical weight computation,
    and move classification.

    Args:
        board: Chess board position

    Returns:
        Tuple of (contact_ratio, total_moves, capture_moves, checking_moves)
        - contact_ratio: 0.0-1.0, proportion of contact moves
        - total_moves: Total number of legal moves
        - capture_moves: Number of capturing moves
        - checking_moves: Number of non-capture checking moves
    """
    total_moves = 0
    capture_moves = 0
    checking_moves = 0

    for mv in board.legal_moves:
        total_moves += 1
        if board.is_capture(mv):
            capture_moves += 1
        else:
            # Only count as checking move if not a capture
            board.push(mv)
            if board.is_check():
                checking_moves += 1
            board.pop()

    contact_moves = capture_moves + checking_moves
    ratio = (contact_moves / total_moves) if total_moves else 0.0

    return ratio, total_moves, capture_moves, checking_moves


def contact_ratio(board: chess.Board) -> float:
    """
    Get just the contact ratio (simplified interface).

    Args:
        board: Chess board position

    Returns:
        Contact ratio as float 0.0-1.0
    """
    ratio, _, _, _ = contact_profile(board)
    return ratio


__all__ = ["contact_profile", "contact_ratio"]
