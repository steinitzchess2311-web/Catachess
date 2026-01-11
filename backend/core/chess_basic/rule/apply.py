"""
chess_basic.rule.apply
合法走法应用并生成新棋盘状态

Apply legal moves and generate new board state.
"""

from copy import deepcopy
from ..types import BoardState, Move, Square, Piece
from ..constants import Color, PieceType, CastlingRight


def apply_legal_move(state: BoardState, move: Move) -> BoardState:
    """
    应用合法走法（假设已验证合法性）
    Apply legal move (assumes move has been validated)

    Args:
        state: Current board state
        move: Legal move to apply

    Returns:
        New board state after applying move
    """
    return apply_move_unchecked(state, move)


def apply_move_unchecked(state: BoardState, move: Move) -> BoardState:
    """
    应用走法（不检查合法性）
    Apply move without legality checking

    Args:
        state: Current board state
        move: Move to apply

    Returns:
        New board state after applying move
    """
    # 创建新状态 Create new state
    new_state = state.copy()

    piece = new_state.get_piece(move.from_square)
    if piece is None:
        return new_state  # 不应该发生 Shouldn't happen

    # 检查特殊走法 Check for special moves
    is_capture = new_state.get_piece(move.to_square) is not None
    is_pawn_move = piece.piece_type == PieceType.PAWN

    # 处理王车易位 Handle castling
    if piece.piece_type == PieceType.KING:
        file_diff = move.to_square.file - move.from_square.file
        if abs(file_diff) == 2:
            # 这是王车易位 This is castling
            _apply_castling(new_state, move, piece.color, file_diff > 0)
            _update_state_after_move(new_state, False, False)
            return new_state

    # 处理吃过路兵 Handle en passant
    en_passant_capture = False
    if is_pawn_move and new_state.en_passant_square == move.to_square:
        en_passant_capture = True
        # 移除被吃的兵 Remove captured pawn
        capture_rank = move.from_square.rank
        captured_pawn_square = Square(move.to_square.file, capture_rank)
        new_state.set_piece(captured_pawn_square, None)
        is_capture = True

    # 移动棋子 Move piece
    new_state.set_piece(move.from_square, None)

    # 处理升变 Handle promotion
    if move.promotion:
        promoted_piece = Piece(piece.color, move.promotion)
        new_state.set_piece(move.to_square, promoted_piece)
    else:
        new_state.set_piece(move.to_square, piece)

    # 更新王车易位权利 Update castling rights
    _update_castling_rights(new_state, move, piece)

    # 设置吃过路兵目标 Set en passant target
    new_en_passant = None
    if is_pawn_move:
        rank_diff = abs(move.to_square.rank - move.from_square.rank)
        if rank_diff == 2:
            # 兵前进两步，设置吃过路兵目标 Pawn moved two squares, set en passant target
            ep_rank = (move.from_square.rank + move.to_square.rank) // 2
            new_en_passant = Square(move.from_square.file, ep_rank)

    new_state.en_passant_square = new_en_passant

    # 更新半回合计数和全回合数 Update halfmove clock and fullmove number
    _update_state_after_move(new_state, is_capture, is_pawn_move)

    return new_state


def _apply_castling(state: BoardState, king_move: Move, color: Color, is_kingside: bool) -> None:
    """
    应用王车易位
    Apply castling move

    Args:
        state: Board state to modify
        king_move: King's move
        color: Color performing castling
        is_kingside: True for kingside, False for queenside
    """
    # 移动王 Move king
    king = state.get_piece(king_move.from_square)
    state.set_piece(king_move.from_square, None)
    state.set_piece(king_move.to_square, king)

    # 移动车 Move rook
    rook_from_file = 7 if is_kingside else 0
    rook_to_file = 5 if is_kingside else 3
    rank = 0 if color == Color.WHITE else 7

    rook_from = Square(rook_from_file, rank)
    rook_to = Square(rook_to_file, rank)

    rook = state.get_piece(rook_from)
    state.set_piece(rook_from, None)
    state.set_piece(rook_to, rook)


def _update_castling_rights(state: BoardState, move: Move, piece: Piece) -> None:
    """
    更新王车易位权利
    Update castling rights after a move

    Args:
        state: Board state to modify
        move: Move that was made
        piece: Piece that moved
    """
    # 如果王移动，失去该方所有王车易位权利
    # If king moves, lose all castling rights for that color
    if piece.piece_type == PieceType.KING:
        if piece.color == Color.WHITE:
            state.castling_rights.white_kingside = False
            state.castling_rights.white_queenside = False
        else:
            state.castling_rights.black_kingside = False
            state.castling_rights.black_queenside = False

    # 如果车移动，失去该侧王车易位权利
    # If rook moves, lose castling rights for that side
    if piece.piece_type == PieceType.ROOK:
        if piece.color == Color.WHITE:
            if move.from_square == Square(0, 0):  # a1
                state.castling_rights.white_queenside = False
            elif move.from_square == Square(7, 0):  # h1
                state.castling_rights.white_kingside = False
        else:
            if move.from_square == Square(0, 7):  # a8
                state.castling_rights.black_queenside = False
            elif move.from_square == Square(7, 7):  # h8
                state.castling_rights.black_kingside = False

    # 如果车被吃，失去该侧王车易位权利
    # If rook is captured, lose castling rights for that side
    captured_rook_squares = {
        Square(0, 0): (Color.WHITE, False),  # a1, white queenside
        Square(7, 0): (Color.WHITE, True),   # h1, white kingside
        Square(0, 7): (Color.BLACK, False),  # a8, black queenside
        Square(7, 7): (Color.BLACK, True),   # h8, black kingside
    }

    if move.to_square in captured_rook_squares:
        color, is_kingside = captured_rook_squares[move.to_square]
        if color == Color.WHITE:
            if is_kingside:
                state.castling_rights.white_kingside = False
            else:
                state.castling_rights.white_queenside = False
        else:
            if is_kingside:
                state.castling_rights.black_kingside = False
            else:
                state.castling_rights.black_queenside = False


def _update_state_after_move(state: BoardState, is_capture: bool, is_pawn_move: bool) -> None:
    """
    更新状态计数器
    Update state counters after move

    Args:
        state: Board state to modify
        is_capture: Whether move was a capture
        is_pawn_move: Whether a pawn moved
    """
    # 半回合计数：捕获或兵移动时重置
    # Halfmove clock: reset on capture or pawn move
    if is_capture or is_pawn_move:
        state.halfmove_clock = 0
    else:
        state.halfmove_clock += 1

    # 全回合数：黑方走完后增加
    # Fullmove number: increment after black's move
    if state.turn == Color.BLACK:
        state.fullmove_number += 1

    # 切换轮次 Switch turn
    state.turn = state.turn.opposite()
