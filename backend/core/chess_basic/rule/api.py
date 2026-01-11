"""
chess_basic.rule.api
规则层对外唯一接口

Public API for the rule engine. This is the only module that should be
imported from outside the rule package.
"""

from typing import Optional
from ..types import BoardState, Move
from ..constants import GameResult, TerminationReason
from .legality import is_move_legal
from .apply import apply_legal_move
from .movegen import generate_pseudo_legal_moves
from .check import (
    is_in_check,
    is_in_checkmate,
    is_in_stalemate,
    has_insufficient_material,
)


def is_legal_move(state: BoardState, move: Move) -> bool:
    """
    检查走法是否合法
    Check if move is legal

    Args:
        state: Current board state
        move: Move to check

    Returns:
        True if move is legal, False otherwise
    """
    return is_move_legal(state, move)


def apply_move(state: BoardState, move: Move) -> BoardState:
    """
    应用合法走法并返回新棋盘状态
    Apply legal move and return new board state

    This function assumes the move is legal. Call is_legal_move first to verify.

    Args:
        state: Current board state
        move: Move to apply (must be legal)

    Returns:
        New board state after applying the move

    Raises:
        IllegalMoveError: If move is illegal
    """
    if not is_move_legal(state, move):
        from ..errors import IllegalMoveError
        raise IllegalMoveError(f"Move {move.to_uci()} is not legal")

    return apply_legal_move(state, move)


def generate_legal_moves(state: BoardState) -> list[Move]:
    """
    生成所有合法走法
    Generate all legal moves for current position

    Args:
        state: Current board state

    Returns:
        List of all legal moves
    """
    pseudo_legal = generate_pseudo_legal_moves(state)
    legal = []

    for move in pseudo_legal:
        if is_move_legal(state, move):
            legal.append(move)

    return legal


def is_check(state: BoardState) -> bool:
    """
    检查当前方是否被将军
    Check if current side is in check

    Args:
        state: Current board state

    Returns:
        True if in check, False otherwise
    """
    return is_in_check(state, state.turn)


def is_checkmate(state: BoardState) -> bool:
    """
    检查当前方是否被将死
    Check if current side is in checkmate

    Args:
        state: Current board state

    Returns:
        True if in checkmate, False otherwise
    """
    return is_in_checkmate(state)


def is_stalemate(state: BoardState) -> bool:
    """
    检查是否为逼和
    Check if position is stalemate

    Args:
        state: Current board state

    Returns:
        True if stalemate, False otherwise
    """
    return is_in_stalemate(state)


def is_game_over(state: BoardState) -> bool:
    """
    检查对局是否结束
    Check if game is over

    Args:
        state: Current board state

    Returns:
        True if game is over, False otherwise
    """
    return (
        is_in_checkmate(state)
        or is_in_stalemate(state)
        or has_insufficient_material(state)
        or state.halfmove_clock >= 100  # 50-move rule (100 halfmoves)
    )


def get_game_result(state: BoardState) -> tuple[GameResult, Optional[TerminationReason]]:
    """
    获取对局结果
    Get game result

    Args:
        state: Current board state

    Returns:
        Tuple of (result, reason) or (IN_PROGRESS, None) if game not over
    """
    if is_in_checkmate(state):
        from ..constants import Color
        winner = Color.WHITE if state.turn == Color.BLACK else Color.BLACK
        result = GameResult.WHITE_WINS if winner == Color.WHITE else GameResult.BLACK_WINS
        return (result, TerminationReason.CHECKMATE)

    if is_in_stalemate(state):
        return (GameResult.DRAW, TerminationReason.STALEMATE)

    if has_insufficient_material(state):
        return (GameResult.DRAW, TerminationReason.INSUFFICIENT_MATERIAL)

    if state.halfmove_clock >= 100:
        return (GameResult.DRAW, TerminationReason.FIFTY_MOVE_RULE)

    return (GameResult.IN_PROGRESS, None)
