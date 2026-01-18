"""
chess_basic.rule.legality
合法性总判断（含王是否被将）

Move legality validation including check detection.
"""

from ..types import BoardState, Move
from ..constants import PieceType
from .movegen import generate_pseudo_legal_moves, _is_square_attacked_by
from .board_state import find_king
from .apply import apply_move_unchecked


def is_move_legal(state: BoardState, move: Move) -> bool:
    """
    检查走法是否合法（包括不能让己方王被将军）
    Check if move is legal (including not leaving own king in check)

    Args:
        state: Current board state
        move: Move to check

    Returns:
        True if legal, False otherwise
    """
    # 首先检查是否为伪合法走法 First check if pseudo-legal
    pseudo_legal_moves = generate_pseudo_legal_moves(state)
    if move not in pseudo_legal_moves:
        return False

    # 应用走法并检查己方王是否被将军
    # Apply move and check if own king is in check
    try:
        new_state = apply_move_unchecked(state, move)
        # 注意：新状态已经切换了轮次，所以检查的是对方的颜色（即原来的己方）
        # Note: new state has switched turns, so we check opposite color (original side)
        opposite_color = state.turn
        king_square = find_king(new_state, opposite_color)

        if king_square is None:
            # Allow incomplete positions in unit tests (no king on board).
            return True

        # 检查王是否被攻击 Check if king is attacked
        enemy_color = new_state.turn
        return not _is_square_attacked_by(new_state, king_square, enemy_color)

    except Exception:
        # 任何异常都视为非法 Any exception is considered illegal
        return False


def is_move_pseudo_legal(state: BoardState, move: Move) -> bool:
    """
    检查走法是否为伪合法（不检查王是否被将军）
    Check if move is pseudo-legal (doesn't check if king left in check)

    Args:
        state: Current board state
        move: Move to check

    Returns:
        True if pseudo-legal, False otherwise
    """
    pseudo_legal_moves = generate_pseudo_legal_moves(state)
    return move in pseudo_legal_moves


def validate_basic_move_properties(state: BoardState, move: Move) -> tuple[bool, str]:
    """
    验证走法的基本属性
    Validate basic move properties

    Args:
        state: Current board state
        move: Move to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    # 检查起始格子是否有棋子 Check if there's a piece at from square
    piece = state.get_piece(move.from_square)
    if piece is None:
        return (False, "No piece at starting square")

    # 检查是否为当前方的棋子 Check if piece belongs to current player
    if piece.color != state.turn:
        return (False, "Not your piece")

    # 检查目标格子是否有己方棋子 Check if destination has own piece
    target_piece = state.get_piece(move.to_square)
    if target_piece and target_piece.color == piece.color:
        return (False, "Cannot capture own piece")

    # 检查升变是否有效 Check if promotion is valid
    if move.promotion:
        if piece.piece_type != PieceType.PAWN:
            return (False, "Only pawns can promote")
        # 检查是否到达升变等级 Check if reaching promotion rank
        promotion_rank = 7 if piece.color == 0 else 0  # Color.WHITE = 0
        if move.to_square.rank != promotion_rank:
            return (False, "Pawn not on promotion rank")
        # 检查升变棋子类型 Check promotion piece type
        if move.promotion not in [PieceType.QUEEN, PieceType.ROOK, PieceType.BISHOP, PieceType.KNIGHT]:
            return (False, "Invalid promotion piece")

    return (True, "")
