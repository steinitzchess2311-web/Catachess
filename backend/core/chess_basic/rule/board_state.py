"""
chess_basic.rule.board_state
棋盘状态数据结构与初始化

Board state initialization and helper functions.
"""

from typing import Optional
from ..types import BoardState, Piece, Square
from ..constants import Color, PieceType, STARTING_FEN
from ..utils.fen import parse_fen


def create_starting_position() -> BoardState:
    """
    创建起始棋盘位置
    Create starting board position

    Returns:
        BoardState with starting position
    """
    return parse_fen(STARTING_FEN)


def find_king(state: BoardState, color: Color) -> Optional[Square]:
    """
    查找指定颜色的王
    Find king of specified color

    Args:
        state: Current board state
        color: Color of king to find

    Returns:
        Square where king is located, or None if not found
    """
    for index in range(64):
        piece = state.board[index]
        if piece and piece.color == color and piece.piece_type == PieceType.KING:
            return Square.from_index(index)
    return None


def get_pieces_of_color(state: BoardState, color: Color) -> list[tuple[Square, Piece]]:
    """
    获取指定颜色的所有棋子及其位置
    Get all pieces of specified color with their positions

    Args:
        state: Current board state
        color: Color of pieces to find

    Returns:
        List of (square, piece) tuples
    """
    pieces = []
    for index in range(64):
        piece = state.board[index]
        if piece and piece.color == color:
            square = Square.from_index(index)
            pieces.append((square, piece))
    return pieces


def count_pieces(state: BoardState) -> dict[tuple[Color, PieceType], int]:
    """
    统计棋盘上的棋子数量
    Count pieces on the board

    Args:
        state: Current board state

    Returns:
        Dictionary mapping (color, piece_type) to count
    """
    counts: dict[tuple[Color, PieceType], int] = {}

    for index in range(64):
        piece = state.board[index]
        if piece:
            key = (piece.color, piece.piece_type)
            counts[key] = counts.get(key, 0) + 1

    return counts


def is_square_attacked(state: BoardState, square: Square, by_color: Color) -> bool:
    """
    检查指定格子是否被指定颜色的棋子攻击
    Check if square is attacked by specified color

    Args:
        state: Current board state
        square: Square to check
        by_color: Color of attacking pieces

    Returns:
        True if square is attacked, False otherwise
    """
    # 这个函数将在 movegen.py 中实现完整逻辑
    # This function's full logic will be implemented in movegen.py
    # 这里是占位符 This is a placeholder
    from .movegen import _is_square_attacked_by
    return _is_square_attacked_by(state, square, by_color)
