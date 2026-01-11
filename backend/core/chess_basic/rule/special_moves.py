"""
chess_basic.rule.special_moves
王车易位、升变、吃过路兵规则

Special move rules: castling, promotion, en passant.
"""

from ..types import BoardState, Move, Square, Piece
from ..constants import Color, PieceType, CastlingRight
from .movegen import _is_square_attacked_by


def generate_castling_moves(state: BoardState, king_square: Square, king: Piece) -> list[Move]:
    """
    生成王车易位走法
    Generate castling moves

    Args:
        state: Current board state
        king_square: Square where king is located
        king: King piece

    Returns:
        List of legal castling moves
    """
    moves = []
    color = king.color

    # 检查王是否被将军 Check if king is in check
    if _is_square_attacked_by(state, king_square, color.opposite()):
        return moves  # 不能在被将军时王车易位 Cannot castle while in check

    # 检查王车易位权利 Check castling rights
    if color == Color.WHITE:
        rank = 0
        if state.castling_rights.white_kingside:
            kingside_move = _try_castling(state, king_square, color, True, rank)
            if kingside_move:
                moves.append(kingside_move)

        if state.castling_rights.white_queenside:
            queenside_move = _try_castling(state, king_square, color, False, rank)
            if queenside_move:
                moves.append(queenside_move)
    else:
        rank = 7
        if state.castling_rights.black_kingside:
            kingside_move = _try_castling(state, king_square, color, True, rank)
            if kingside_move:
                moves.append(kingside_move)

        if state.castling_rights.black_queenside:
            queenside_move = _try_castling(state, king_square, color, False, rank)
            if queenside_move:
                moves.append(queenside_move)

    return moves


def _try_castling(
    state: BoardState,
    king_square: Square,
    color: Color,
    is_kingside: bool,
    rank: int
) -> Move | None:
    """
    尝试生成王车易位走法
    Try to generate castling move

    Args:
        state: Current board state
        king_square: King's current square
        color: Color of king
        is_kingside: True for kingside, False for queenside
        rank: Rank of castling (0 for white, 7 for black)

    Returns:
        Castling move if legal, None otherwise
    """
    # 王车易位路径 Castling path
    if is_kingside:
        # 王侧：王从 e 到 g，路径 f 必须为空且不被攻击
        # Kingside: King from e to g, f must be empty and not attacked
        target_file = 6  # g file
        path_files = [5, 6]  # f, g
    else:
        # 后侧：王从 e 到 c，路径 d, c 必须为空，d 不被攻击
        # Queenside: King from e to c, d and c must be empty, d not attacked
        target_file = 2  # c file
        path_files = [3, 2]  # d, c
        # b 也必须为空 b must also be empty
        b_square = Square(1, rank)
        if state.get_piece(b_square) is not None:
            return None

    # 检查路径是否为空 Check if path is clear
    for file in path_files:
        square = Square(file, rank)
        if state.get_piece(square) is not None:
            return None

    # 检查王经过的格子是否被攻击 Check if squares king passes through are attacked
    check_files = [4, 5, 6] if is_kingside else [4, 3, 2]
    for file in check_files:
        square = Square(file, rank)
        if _is_square_attacked_by(state, square, color.opposite()):
            return None

    # 王车易位合法 Castling is legal
    target_square = Square(target_file, rank)
    return Move(king_square, target_square)


def is_en_passant_capture(state: BoardState, move: Move) -> bool:
    """
    检查走法是否为吃过路兵
    Check if move is en passant capture

    Args:
        state: Current board state
        move: Move to check

    Returns:
        True if en passant capture, False otherwise
    """
    piece = state.get_piece(move.from_square)
    if not piece or piece.piece_type != PieceType.PAWN:
        return False

    return state.en_passant_square == move.to_square


def is_castling_move(state: BoardState, move: Move) -> bool:
    """
    检查走法是否为王车易位
    Check if move is castling

    Args:
        state: Current board state
        move: Move to check

    Returns:
        True if castling, False otherwise
    """
    piece = state.get_piece(move.from_square)
    if not piece or piece.piece_type != PieceType.KING:
        return False

    file_diff = abs(move.to_square.file - move.from_square.file)
    return file_diff == 2


def is_promotion_move(state: BoardState, move: Move) -> bool:
    """
    检查走法是否为升变
    Check if move is promotion

    Args:
        state: Current board state
        move: Move to check

    Returns:
        True if promotion, False otherwise
    """
    return move.promotion is not None


def get_captured_piece_square(state: BoardState, move: Move) -> Square | None:
    """
    获取被捕获棋子的格子（处理吃过路兵的特殊情况）
    Get square of captured piece (handles en passant special case)

    Args:
        state: Current board state
        move: Move being made

    Returns:
        Square of captured piece, or None if no capture
    """
    # 检查目标格子是否有棋子 Check if target square has piece
    if state.get_piece(move.to_square) is not None:
        return move.to_square

    # 检查是否为吃过路兵 Check if en passant
    if is_en_passant_capture(state, move):
        piece = state.get_piece(move.from_square)
        if piece:
            # 被捕获的兵在起始格子的同一等级
            # Captured pawn is on same rank as starting square
            return Square(move.to_square.file, move.from_square.rank)

    return None
