"""
chess_basic.rule.check
将军、将死、逼和判断

Check, checkmate, and stalemate detection.
"""

from ..types import BoardState
from ..constants import Color, PieceType
from .board_state import find_king, count_pieces
from .movegen import _is_square_attacked_by, generate_pseudo_legal_moves


def is_in_check(state: BoardState, color: Color) -> bool:
    """
    检查指定方是否被将军
    Check if specified color is in check

    Args:
        state: Current board state
        color: Color to check

    Returns:
        True if in check, False otherwise
    """
    king_square = find_king(state, color)
    if king_square is None:
        return False  # 王不存在（不应该发生）King doesn't exist (shouldn't happen)

    return _is_square_attacked_by(state, king_square, color.opposite())


def is_in_checkmate(state: BoardState) -> bool:
    """
    检查当前方是否被将死
    Check if current side is in checkmate

    Args:
        state: Current board state

    Returns:
        True if in checkmate, False otherwise
    """
    # 必须被将军 Must be in check
    if not is_in_check(state, state.turn):
        return False

    # 没有合法走法 No legal moves
    return not _has_legal_move(state)


def is_in_stalemate(state: BoardState) -> bool:
    """
    检查是否为逼和
    Check if position is stalemate

    Args:
        state: Current board state

    Returns:
        True if stalemate, False otherwise
    """
    # 不能被将军 Must not be in check
    if is_in_check(state, state.turn):
        return False

    # 没有合法走法 No legal moves
    return not _has_legal_move(state)


def _has_legal_move(state: BoardState) -> bool:
    """
    检查是否有合法走法
    Check if there are any legal moves

    Args:
        state: Current board state

    Returns:
        True if at least one legal move exists, False otherwise
    """
    from .legality import is_move_legal

    pseudo_legal = generate_pseudo_legal_moves(state)
    for move in pseudo_legal:
        if is_move_legal(state, move):
            return True

    return False


def has_insufficient_material(state: BoardState) -> bool:
    """
    检查是否子力不足无法将死
    Check if insufficient material to checkmate

    Scenarios:
    - King vs King
    - King + Bishop vs King
    - King + Knight vs King
    - King + Bishop vs King + Bishop (same color square)

    Args:
        state: Current board state

    Returns:
        True if insufficient material, False otherwise
    """
    pieces = count_pieces(state)

    # 统计每方的棋子 Count pieces for each side
    white_pieces = {pt: pieces.get((Color.WHITE, pt), 0) for pt in PieceType}
    black_pieces = {pt: pieces.get((Color.BLACK, pt), 0) for pt in PieceType}

    # 统计总棋子数（不含王）Count total pieces (excluding kings)
    white_count = sum(count for pt, count in white_pieces.items() if pt != PieceType.KING)
    black_count = sum(count for pt, count in black_pieces.items() if pt != PieceType.KING)

    total_pieces = white_count + black_count

    # 王对王 King vs King
    if total_pieces == 0:
        return True

    # 王+轻子 vs 王 King + minor piece vs King
    if total_pieces == 1:
        # 检查是否只有一个象或马 Check if only one bishop or knight
        has_only_bishop = (white_pieces[PieceType.BISHOP] == 1 and white_count == 1) or \
                         (black_pieces[PieceType.BISHOP] == 1 and black_count == 1)
        has_only_knight = (white_pieces[PieceType.KNIGHT] == 1 and white_count == 1) or \
                         (black_pieces[PieceType.KNIGHT] == 1 and black_count == 1)
        return has_only_bishop or has_only_knight

    # 王+象 vs 王+象（同色格）King + Bishop vs King + Bishop (same color squares)
    if total_pieces == 2:
        if white_pieces[PieceType.BISHOP] == 1 and black_pieces[PieceType.BISHOP] == 1:
            # 需要检查象是否在同色格（简化实现：假设可能将死）
            # Would need to check if bishops on same color squares (simplified: assume can checkmate)
            # 完整实现需要检查象的位置 Full implementation would check bishop positions
            return False

    return False


def gives_check(state: BoardState, move: "Move") -> bool:
    """
    检查走法是否会将军对方
    Check if move gives check to opponent

    Args:
        state: Current board state before move
        move: Move to check

    Returns:
        True if move gives check, False otherwise
    """
    from .apply import apply_move_unchecked

    # 应用走法 Apply move
    new_state = apply_move_unchecked(state, move)

    # 检查对方是否被将军 Check if opponent is in check
    return is_in_check(new_state, new_state.turn)
