"""
Sacrifice detection helpers.

This module provides helper functions for detecting and classifying sacrifice moves -
moves where the player voluntarily gives up material for compensation.

Key concepts:
- Sacrifice: Material loss ≥ 0.5 pawns where opponent can win material
- Tactical sacrifice: Sacrifice with opponent king safety drop
- Positional sacrifice: Sacrifice without king attack
- Even exchange: Equal value trade (not a sacrifice)

Functions:
- is_sacrifice_candidate(): Detect if move sacrifices material
- compute_material_delta(): Calculate material loss
- is_even_exchange(): Check if move offers equal trade
- classify_sacrifice_quality(): Classify sacrifice type based on compensation
"""
from typing import Tuple, Dict
import chess
from ...models import TagContext

# Piece values in pawns
PIECE_VALUES = {
    chess.PAWN: 1.0,
    chess.KNIGHT: 3.0,
    chess.BISHOP: 3.0,
    chess.ROOK: 5.0,
    chess.QUEEN: 9.0,
    chess.KING: 0.0,
}

# Thresholds
SACRIFICE_MIN_LOSS = 0.5  # Minimum material loss (pawns) to be sacrifice
SACRIFICE_EVAL_TOLERANCE = 0.6  # Max eval drop for "sound" sacrifice
SACRIFICE_KING_DROP_THRESHOLD = -0.1  # Opponent king safety drop for tactical
EXCHANGE_EVAL_TOLERANCE = 0.15  # Near-equal eval = even exchange (not sacrifice)


def get_piece_value(piece_type: int) -> float:
    """Get material value of a piece type in pawns."""
    return PIECE_VALUES.get(piece_type, 0.0)


def compute_captured_value(board: chess.Board, move: chess.Move) -> float:
    """
    Compute value of captured piece (if any).

    Handles en passant captures correctly.

    Args:
        board: Position before move
        move: The move being evaluated

    Returns:
        Material value of captured piece in pawns
    """
    if not board.is_capture(move):
        return 0.0

    # Handle en passant
    if board.is_en_passant(move):
        return PIECE_VALUES[chess.PAWN]

    # Normal capture
    captured_piece = board.piece_at(move.to_square)
    if captured_piece is None:
        return 0.0

    return PIECE_VALUES.get(captured_piece.piece_type, 0.0)


def compute_material_delta(board: chess.Board, move: chess.Move) -> float:
    """
    Compute net material loss for the moving side.

    Positive value = material loss (sacrifice)
    Negative value = material gain
    Zero = even trade

    Args:
        board: Position before move
        move: The move being evaluated

    Returns:
        Material delta in pawns (positive = loss)
    """
    piece = board.piece_at(move.from_square)
    if piece is None:
        return 0.0

    piece_value = PIECE_VALUES.get(piece.piece_type, 0.0)
    captured_value = compute_captured_value(board, move)

    return piece_value - captured_value


def opponent_wins_material(
    board_after: chess.Board,
    target_square: int,
    material_at_risk: float
) -> bool:
    """
    Check if opponent can profitably capture on target square.

    Args:
        board_after: Position after the move
        target_square: Square where piece landed
        material_at_risk: Value of piece on target square

    Returns:
        True if opponent has profitable capture available
    """
    opponent = board_after.turn
    attackers = board_after.attackers(opponent, target_square)

    if not attackers:
        return False

    # Check if any attacker is worth less than or equal to material at risk
    for attacker_sq in attackers:
        attacker_piece = board_after.piece_at(attacker_sq)
        if attacker_piece is None:
            continue
        attacker_value = PIECE_VALUES.get(attacker_piece.piece_type, 0.0)
        if attacker_value <= material_at_risk:
            return True

    return False


def is_sacrifice_candidate(ctx: TagContext) -> Tuple[bool, Dict[str, float]]:
    """
    Detect if move is a sacrifice candidate.

    A sacrifice must:
    1. Lose material (≥ 0.5 pawns)
    2. Allow opponent to win material
    3. Not be an even exchange

    Args:
        ctx: Tag detection context

    Returns:
        Tuple of (is_sacrifice, evidence_dict)
    """
    board = ctx.board
    move = ctx.played_move

    evidence = {}

    # Compute material delta
    material_delta = compute_material_delta(board, move)
    evidence["material_delta"] = material_delta

    # Gate 1: Material loss threshold
    if material_delta < SACRIFICE_MIN_LOSS:
        evidence["reason"] = "insufficient_material_loss"
        return False, evidence

    # Create after-move board
    board_after = board.copy()
    board_after.push(move)

    # Gate 2: Opponent can win material
    piece = board.piece_at(move.from_square)
    if piece is None:
        evidence["reason"] = "no_piece"
        return False, evidence

    piece_value = PIECE_VALUES.get(piece.piece_type, 0.0)
    if not opponent_wins_material(board_after, move.to_square, piece_value):
        evidence["reason"] = "opponent_cannot_capture"
        return False, evidence

    # Gate 3: Not an even exchange
    eval_delta = ctx.delta_eval
    if abs(eval_delta) <= EXCHANGE_EVAL_TOLERANCE:
        evidence["reason"] = "even_exchange"
        return False, evidence

    evidence["reason"] = "is_sacrifice"
    return True, evidence


__all__ = [
    "is_sacrifice_candidate",
    "compute_material_delta",
    "compute_captured_value",
    "opponent_wins_material",
    "get_piece_value",
    "PIECE_VALUES",
    "SACRIFICE_MIN_LOSS",
    "SACRIFICE_EVAL_TOLERANCE",
    "SACRIFICE_KING_DROP_THRESHOLD",
]
