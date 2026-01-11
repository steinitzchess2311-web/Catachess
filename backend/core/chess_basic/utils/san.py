"""
chess_basic.utils.san
SAN 表示法生成（不做合法性判断）

SAN (Standard Algebraic Notation) generation (without legality checking).

Note: This module only formats moves as SAN strings. It does NOT validate
whether moves are legal - that's the responsibility of the rule module.
"""

from typing import Optional
from ..types import Move, BoardState, Piece, Square
from ..constants import PieceType, Color, PIECE_SYMBOLS


def move_to_san(
    move: Move,
    state: BoardState,
    *,
    is_check: bool = False,
    is_checkmate: bool = False,
    is_capture: bool = False,
    disambiguation: Optional[str] = None,
) -> str:
    """
    将走法转换为 SAN 字符串
    Convert move to SAN string

    Note: This function formats the move but does NOT verify legality.
    The caller must ensure the move is legal and provide correct flags.

    Args:
        move: Move object
        state: Board state before the move
        is_check: Whether move gives check
        is_checkmate: Whether move gives checkmate
        is_capture: Whether move is a capture
        disambiguation: File, rank, or square for disambiguation (e.g., 'a', '1', 'a1')

    Returns:
        SAN string (e.g., 'e4', 'Nf3', 'Bxe5+', 'O-O', 'e8=Q#')
    """
    piece = state.get_piece(move.from_square)
    if piece is None:
        # 不应该发生，但返回 UCI 作为后备 Shouldn't happen, but return UCI as fallback
        return move.to_uci()

    # 检查是否为王车易位 Check for castling
    if piece.piece_type == PieceType.KING:
        file_diff = move.to_square.file - move.from_square.file
        if abs(file_diff) == 2:
            return "O-O" if file_diff > 0 else "O-O-O"

    san = ""

    # 棋子符号（兵除外）Piece symbol (except pawns)
    if piece.piece_type != PieceType.PAWN:
        san += PIECE_SYMBOLS[piece.piece_type].upper()

        # 消歧义 Disambiguation
        if disambiguation:
            san += disambiguation

    # 兵的捕获需要起始文件 Pawn captures need starting file
    elif is_capture:
        san += chr(ord('a') + move.from_square.file)

    # 捕获符号 Capture symbol
    if is_capture:
        san += "x"

    # 目标格子 Destination square
    san += move.to_square.to_algebraic()

    # 升变 Promotion
    if move.promotion:
        san += "=" + PIECE_SYMBOLS[move.promotion].upper()

    # 将军/将死 Check/checkmate
    if is_checkmate:
        san += "#"
    elif is_check:
        san += "+"

    return san


def format_castle_move(is_kingside: bool) -> str:
    """
    格式化王车易位走法
    Format castling move

    Args:
        is_kingside: True for kingside castling, False for queenside

    Returns:
        SAN string ('O-O' or 'O-O-O')
    """
    return "O-O" if is_kingside else "O-O-O"


def needs_disambiguation(
    piece: Piece,
    from_square: Square,
    to_square: Square,
    state: BoardState,
    legal_moves: list[Move],
) -> Optional[str]:
    """
    确定是否需要消歧义以及消歧义字符
    Determine if disambiguation is needed and what character to use

    This is used when multiple pieces of the same type can move to the same square.

    Args:
        piece: Piece being moved
        from_square: Starting square
        to_square: Destination square
        state: Current board state
        legal_moves: List of all legal moves in current position

    Returns:
        Disambiguation string ('a'-'h', '1'-'8', or 'a1'-'h8'), or None if not needed
    """
    if piece.piece_type == PieceType.PAWN:
        # 兵不需要文件以外的消歧义 Pawns only need file, handled separately
        return None

    # 查找所有可以移动到目标格子的同类棋子
    # Find all pieces of same type that can move to destination
    ambiguous_moves = []
    for legal_move in legal_moves:
        if legal_move.to_square == to_square:
            other_piece = state.get_piece(legal_move.from_square)
            if (
                other_piece
                and other_piece.piece_type == piece.piece_type
                and other_piece.color == piece.color
                and legal_move.from_square != from_square
            ):
                ambiguous_moves.append(legal_move)

    if not ambiguous_moves:
        return None  # 不需要消歧义 No disambiguation needed

    # 尝试使用文件消歧义 Try file disambiguation
    same_file = any(m.from_square.file == from_square.file for m in ambiguous_moves)
    if not same_file:
        return chr(ord('a') + from_square.file)

    # 尝试使用等级消歧义 Try rank disambiguation
    same_rank = any(m.from_square.rank == from_square.rank for m in ambiguous_moves)
    if not same_rank:
        return str(from_square.rank + 1)

    # 需要完整格子消歧义 Need full square disambiguation
    return from_square.to_algebraic()
