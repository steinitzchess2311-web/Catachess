"""
Game phase detection for chess positions.

Estimates the game phase (opening/middlegame/endgame) based on remaining
material. This affects threshold settings for various tag detectors.
"""
import chess


def estimate_phase_ratio(board: chess.Board) -> float:
    """
    Estimate game phase as a ratio from 0.0 (endgame) to 1.0 (opening).

    Phase is computed by counting remaining pieces weighted by their
    contribution to game complexity. More pieces = earlier phase.

    Phase weights (from legacy):
    - Pawn: 0 (pawns don't affect phase)
    - Knight/Bishop: 1 each
    - Rook: 2 each
    - Queen: 4 each

    Starting position has 24 phase points (4N + 4B + 4R + 2Q).

    Args:
        board: Chess board position

    Returns:
        Phase ratio 0.0-1.0:
        - 1.0 = Opening (all pieces on board)
        - 0.5 = Middlegame (half pieces remain)
        - 0.0 = Endgame (minimal material)
    """
    phase_weights = {
        chess.PAWN: 0,
        chess.KNIGHT: 1,
        chess.BISHOP: 1,
        chess.ROOK: 2,
        chess.QUEEN: 4,
    }

    total_phase = 24  # Starting phase: 4*1 + 4*1 + 4*2 + 2*4 = 24
    current_phase = 0

    for piece_type, weight in phase_weights.items():
        if weight == 0:
            continue
        for color in (chess.WHITE, chess.BLACK):
            current_phase += weight * len(board.pieces(piece_type, color))

    return current_phase / total_phase if total_phase else 0.0


def get_phase_bucket(phase_ratio: float) -> str:
    """
    Convert phase ratio to phase bucket label.

    Args:
        phase_ratio: Phase ratio from estimate_phase_ratio()

    Returns:
        Phase bucket: "endgame", "middlegame", or "opening"
    """
    if phase_ratio <= 0.33:
        return "endgame"
    if phase_ratio <= 0.66:
        return "middlegame"
    return "opening"


__all__ = ["estimate_phase_ratio", "get_phase_bucket"]
