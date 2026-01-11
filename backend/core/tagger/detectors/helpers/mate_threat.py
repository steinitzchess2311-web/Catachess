"""
Mate threat detection helper.
Detects when there's a checkmate threat in the position.
"""
from typing import List
import chess

from ...models import Candidate


def detect_mate_threat(
    board: chess.Board,
    candidates: List[Candidate],
    eval_before_cp: int,
) -> bool:
    """
    Detect if there's a mate threat in the position.

    A mate threat exists when:
    1. Best move leads to mate (score >= 9000)
    2. Player has a forcing move that threatens mate
    3. Opponent was threatening mate (eval_before <= -9000)

    Args:
        board: Current board position
        candidates: List of candidate moves
        eval_before_cp: Evaluation before move (centipawns)

    Returns:
        True if mate threat exists
    """
    # Check if opponent was threatening mate
    if eval_before_cp <= -9000:
        return True

    # Check if best move threatens/achieves mate
    if candidates:
        best_score = candidates[0].score_cp
        if best_score >= 9000:
            return True

    # Check if any forcing move threatens mate
    for cand in candidates:
        if cand.kind in ("forcing", "dynamic") and cand.score_cp >= 9000:
            return True

    return False


def get_mate_distance(score_cp: int) -> int:
    """
    Get mate distance from score.

    Args:
        score_cp: Score in centipawns

    Returns:
        Mate in N moves (0 if not mate)
    """
    if abs(score_cp) >= 9000:
        return (10000 - abs(score_cp)) // 100
    return 0


def is_mate_score(score_cp: int) -> bool:
    """Check if score indicates mate."""
    return abs(score_cp) >= 9000


__all__ = [
    "detect_mate_threat",
    "get_mate_distance",
    "is_mate_score",
]
