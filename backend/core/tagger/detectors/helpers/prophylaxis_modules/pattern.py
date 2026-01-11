"""
Prophylaxis pattern detection (canonical motifs).

Matches rule_tagger2/legacy/prophylaxis.py:87-106 exactly.
"""
from typing import Optional
import chess


def prophylaxis_pattern_reason(
    board: chess.Board,
    move: chess.Move,
    opp_trend: float,
    opp_tactics_delta: float,
) -> Optional[str]:
    """
    Detect canonical prophylaxis motifs for telemetry/debugging.

    Args:
        board: Current board position
        move: Move being considered
        opp_trend: Opponent's overall trend
        opp_tactics_delta: Opponent's tactics delta

    Returns:
        String describing the pattern, or None if no pattern matches
    """
    piece = board.piece_at(move.from_square)
    if piece is None:
        return None

    trend_ok = opp_trend <= 0.12 or opp_tactics_delta <= 0.12

    if piece.piece_type == chess.BISHOP and trend_ok:
        return "anticipatory bishop retreat"
    if piece.piece_type == chess.KNIGHT and trend_ok:
        return "anticipatory knight reposition"
    if piece.piece_type == chess.KING and (opp_trend <= 0.15 or opp_tactics_delta <= 0.1):
        return "king safety shuffle"
    if piece.piece_type == chess.PAWN and trend_ok:
        return "pawn advance to restrict opponent play"
    return None
