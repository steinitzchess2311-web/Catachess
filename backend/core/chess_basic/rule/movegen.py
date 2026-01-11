"""
chess_basic.rule.movegen
基础走法生成（不含将军判断）

Pseudo-legal move generation (without check validation).
"""

from typing import Optional
from ..types import BoardState, Move, Piece, Square
from ..constants import Color, PieceType


def generate_pseudo_legal_moves(state: BoardState) -> list[Move]:
    """
    生成所有伪合法走法（不检查是否会导致己方被将军）
    Generate all pseudo-legal moves (doesn't check if king left in check)

    Args:
        state: Current board state

    Returns:
        List of pseudo-legal moves
    """
    moves = []
    turn = state.turn

    for index in range(64):
        piece = state.board[index]
        if piece and piece.color == turn:
            square = Square.from_index(index)
            piece_moves = _generate_piece_moves(state, square, piece)
            moves.extend(piece_moves)

    return moves


def _generate_piece_moves(state: BoardState, square: Square, piece: Piece) -> list[Move]:
    """
    生成单个棋子的所有伪合法走法
    Generate all pseudo-legal moves for a piece

    Args:
        state: Current board state
        square: Square where piece is located
        piece: Piece to generate moves for

    Returns:
        List of pseudo-legal moves for this piece
    """
    if piece.piece_type == PieceType.PAWN:
        return _generate_pawn_moves(state, square, piece)
    elif piece.piece_type == PieceType.KNIGHT:
        return _generate_knight_moves(state, square, piece)
    elif piece.piece_type == PieceType.BISHOP:
        return _generate_bishop_moves(state, square, piece)
    elif piece.piece_type == PieceType.ROOK:
        return _generate_rook_moves(state, square, piece)
    elif piece.piece_type == PieceType.QUEEN:
        return _generate_queen_moves(state, square, piece)
    elif piece.piece_type == PieceType.KING:
        return _generate_king_moves(state, square, piece)
    return []


def _generate_pawn_moves(state: BoardState, square: Square, piece: Piece) -> list[Move]:
    """生成兵的走法 Generate pawn moves"""
    moves = []
    direction = 1 if piece.color == Color.WHITE else -1
    start_rank = 1 if piece.color == Color.WHITE else 6
    promotion_rank = 7 if piece.color == Color.WHITE else 0

    # 向前一步 Forward one square
    forward_rank = square.rank + direction
    if 0 <= forward_rank < 8:
        forward_square = Square(square.file, forward_rank)
        if state.get_piece(forward_square) is None:
            if forward_rank == promotion_rank:
                # 升变 Promotion
                for promo_type in [PieceType.QUEEN, PieceType.ROOK, PieceType.BISHOP, PieceType.KNIGHT]:
                    moves.append(Move(square, forward_square, promo_type))
            else:
                moves.append(Move(square, forward_square))

            # 向前两步（起始位置）Forward two squares (from starting position)
            if square.rank == start_rank:
                forward2_square = Square(square.file, square.rank + 2 * direction)
                if state.get_piece(forward2_square) is None:
                    moves.append(Move(square, forward2_square))

    # 对角捕获 Diagonal captures
    for file_offset in [-1, 1]:
        capture_file = square.file + file_offset
        capture_rank = square.rank + direction
        if 0 <= capture_file < 8 and 0 <= capture_rank < 8:
            capture_square = Square(capture_file, capture_rank)
            target_piece = state.get_piece(capture_square)

            # 普通捕获 Normal capture
            if target_piece and target_piece.color != piece.color:
                if capture_rank == promotion_rank:
                    # 捕获并升变 Capture with promotion
                    for promo_type in [PieceType.QUEEN, PieceType.ROOK, PieceType.BISHOP, PieceType.KNIGHT]:
                        moves.append(Move(square, capture_square, promo_type))
                else:
                    moves.append(Move(square, capture_square))

            # 吃过路兵 En passant
            if state.en_passant_square == capture_square:
                moves.append(Move(square, capture_square))

    return moves


def _generate_knight_moves(state: BoardState, square: Square, piece: Piece) -> list[Move]:
    """生成马的走法 Generate knight moves"""
    moves = []
    knight_offsets = [
        (-2, -1), (-2, 1), (-1, -2), (-1, 2),
        (1, -2), (1, 2), (2, -1), (2, 1)
    ]

    for file_offset, rank_offset in knight_offsets:
        target_file = square.file + file_offset
        target_rank = square.rank + rank_offset

        if 0 <= target_file < 8 and 0 <= target_rank < 8:
            target_square = Square(target_file, target_rank)
            target_piece = state.get_piece(target_square)

            # 空格或捕获敌方棋子 Empty square or capture enemy piece
            if target_piece is None or target_piece.color != piece.color:
                moves.append(Move(square, target_square))

    return moves


def _generate_sliding_moves(
    state: BoardState,
    square: Square,
    piece: Piece,
    directions: list[tuple[int, int]]
) -> list[Move]:
    """生成滑动棋子（车、象、后）的走法 Generate sliding piece moves"""
    moves = []

    for file_dir, rank_dir in directions:
        target_file = square.file + file_dir
        target_rank = square.rank + rank_dir

        while 0 <= target_file < 8 and 0 <= target_rank < 8:
            target_square = Square(target_file, target_rank)
            target_piece = state.get_piece(target_square)

            if target_piece is None:
                # 空格 Empty square
                moves.append(Move(square, target_square))
            else:
                # 遇到棋子 Hit a piece
                if target_piece.color != piece.color:
                    # 捕获敌方棋子 Capture enemy piece
                    moves.append(Move(square, target_square))
                break

            target_file += file_dir
            target_rank += rank_dir

    return moves


def _generate_bishop_moves(state: BoardState, square: Square, piece: Piece) -> list[Move]:
    """生成象的走法 Generate bishop moves"""
    diagonal_directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    return _generate_sliding_moves(state, square, piece, diagonal_directions)


def _generate_rook_moves(state: BoardState, square: Square, piece: Piece) -> list[Move]:
    """生成车的走法 Generate rook moves"""
    orthogonal_directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]
    return _generate_sliding_moves(state, square, piece, orthogonal_directions)


def _generate_queen_moves(state: BoardState, square: Square, piece: Piece) -> list[Move]:
    """生成后的走法 Generate queen moves"""
    all_directions = [
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1)
    ]
    return _generate_sliding_moves(state, square, piece, all_directions)


def _generate_king_moves(state: BoardState, square: Square, piece: Piece) -> list[Move]:
    """生成王的走法（包括王车易位）Generate king moves (including castling)"""
    moves = []

    # 普通王的移动 Normal king moves
    king_offsets = [
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1)
    ]

    for file_offset, rank_offset in king_offsets:
        target_file = square.file + file_offset
        target_rank = square.rank + rank_offset

        if 0 <= target_file < 8 and 0 <= target_rank < 8:
            target_square = Square(target_file, target_rank)
            target_piece = state.get_piece(target_square)

            if target_piece is None or target_piece.color != piece.color:
                moves.append(Move(square, target_square))

    # 王车易位 Castling
    from .special_moves import generate_castling_moves
    castling_moves = generate_castling_moves(state, square, piece)
    moves.extend(castling_moves)

    return moves


def _is_square_attacked_by(state: BoardState, square: Square, by_color: Color) -> bool:
    """
    检查指定格子是否被指定颜色攻击
    Check if square is attacked by specified color

    Args:
        state: Current board state
        square: Square to check
        by_color: Attacking color

    Returns:
        True if attacked, False otherwise
    """
    # 检查兵的攻击 Check pawn attacks
    pawn_direction = -1 if by_color == Color.WHITE else 1
    for file_offset in [-1, 1]:
        pawn_file = square.file + file_offset
        pawn_rank = square.rank + pawn_direction
        if 0 <= pawn_file < 8 and 0 <= pawn_rank < 8:
            pawn_square = Square(pawn_file, pawn_rank)
            piece = state.get_piece(pawn_square)
            if piece and piece.color == by_color and piece.piece_type == PieceType.PAWN:
                return True

    # 检查马的攻击 Check knight attacks
    knight_offsets = [
        (-2, -1), (-2, 1), (-1, -2), (-1, 2),
        (1, -2), (1, 2), (2, -1), (2, 1)
    ]
    for file_offset, rank_offset in knight_offsets:
        knight_file = square.file + file_offset
        knight_rank = square.rank + rank_offset
        if 0 <= knight_file < 8 and 0 <= knight_rank < 8:
            knight_square = Square(knight_file, knight_rank)
            piece = state.get_piece(knight_square)
            if piece and piece.color == by_color and piece.piece_type == PieceType.KNIGHT:
                return True

    # 检查王的攻击 Check king attacks
    for file_offset in [-1, 0, 1]:
        for rank_offset in [-1, 0, 1]:
            if file_offset == 0 and rank_offset == 0:
                continue
            king_file = square.file + file_offset
            king_rank = square.rank + rank_offset
            if 0 <= king_file < 8 and 0 <= king_rank < 8:
                king_square = Square(king_file, king_rank)
                piece = state.get_piece(king_square)
                if piece and piece.color == by_color and piece.piece_type == PieceType.KING:
                    return True

    # 检查滑动棋子的攻击 Check sliding piece attacks
    # 对角线（象、后）Diagonals (bishop, queen)
    diagonal_dirs = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    for file_dir, rank_dir in diagonal_dirs:
        if _check_sliding_attack(state, square, by_color, file_dir, rank_dir, {PieceType.BISHOP, PieceType.QUEEN}):
            return True

    # 直线（车、后）Orthogonals (rook, queen)
    orthogonal_dirs = [(0, -1), (0, 1), (-1, 0), (1, 0)]
    for file_dir, rank_dir in orthogonal_dirs:
        if _check_sliding_attack(state, square, by_color, file_dir, rank_dir, {PieceType.ROOK, PieceType.QUEEN}):
            return True

    return False


def _check_sliding_attack(
    state: BoardState,
    square: Square,
    by_color: Color,
    file_dir: int,
    rank_dir: int,
    piece_types: set[PieceType]
) -> bool:
    """检查滑动攻击 Check sliding attack in a direction"""
    target_file = square.file + file_dir
    target_rank = square.rank + rank_dir

    while 0 <= target_file < 8 and 0 <= target_rank < 8:
        target_square = Square(target_file, target_rank)
        piece = state.get_piece(target_square)

        if piece:
            if piece.color == by_color and piece.piece_type in piece_types:
                return True
            break

        target_file += file_dir
        target_rank += rank_dir

    return False
