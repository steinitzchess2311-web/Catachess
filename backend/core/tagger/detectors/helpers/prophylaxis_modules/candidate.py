"""
Prophylaxis candidate filtering.

Matches rule_tagger2/legacy/prophylaxis.py:109-158 exactly.
"""
import chess

from .config import FULL_MATERIAL_COUNT, OPENING_MOVE_CUTOFF


def is_full_material(board: chess.Board) -> bool:
    """Return True when all 32 pieces remain on the board."""
    return len(board.piece_map()) >= FULL_MATERIAL_COUNT


def is_prophylaxis_candidate(board: chess.Board, move: chess.Move) -> bool:
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
        board: Current board position
        move: Move being considered

    Returns:
        True if move is eligible for prophylaxis tagging
    """
    # Exclude full material opening phase
    if is_full_material(board):
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

    # Exclude very early opening phase
    piece_count = sum(1 for sq in chess.SQUARES if board.piece_at(sq) is not None)
    fullmove_number = board.fullmove_number
    if piece_count >= 32 and fullmove_number < OPENING_MOVE_CUTOFF:
        return False

    return True
