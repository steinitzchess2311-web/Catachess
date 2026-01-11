"""
chess_basic.utils.fen
FEN 解析与序列化

FEN (Forsyth-Edwards Notation) parsing and serialization.
"""

from typing import Optional
from ..types import BoardState, Piece, Square, CastlingRights
from ..constants import Color, STARTING_FEN
from ..errors import FENParseError


def parse_fen(fen: str) -> BoardState:
    """
    解析 FEN 字符串为棋盘状态
    Parse FEN string to board state

    Args:
        fen: FEN string

    Returns:
        BoardState object

    Raises:
        FENParseError: If FEN string is invalid
    """
    try:
        parts = fen.strip().split()
        if len(parts) != 6:
            raise FENParseError(f"FEN must have 6 parts, got {len(parts)}", fen)

        board_part, turn_part, castling_part, ep_part, halfmove_part, fullmove_part = parts

        # 解析棋盘 Parse board
        board = _parse_board_part(board_part)

        # 解析轮次 Parse turn
        if turn_part not in ["w", "b"]:
            raise FENParseError(f"Invalid turn: {turn_part}", fen)
        turn = Color.WHITE if turn_part == "w" else Color.BLACK

        # 解析王车易位权利 Parse castling rights
        castling_rights = CastlingRights.from_fen(castling_part)

        # 解析吃过路兵目标 Parse en passant target
        en_passant_square = None
        if ep_part != "-":
            try:
                en_passant_square = Square.from_algebraic(ep_part)
            except ValueError:
                raise FENParseError(f"Invalid en passant square: {ep_part}", fen)

        # 解析半回合计数 Parse halfmove clock
        try:
            halfmove_clock = int(halfmove_part)
            if halfmove_clock < 0:
                raise ValueError()
        except ValueError:
            raise FENParseError(f"Invalid halfmove clock: {halfmove_part}", fen)

        # 解析全回合数 Parse fullmove number
        try:
            fullmove_number = int(fullmove_part)
            if fullmove_number < 1:
                raise ValueError()
        except ValueError:
            raise FENParseError(f"Invalid fullmove number: {fullmove_part}", fen)

        return BoardState(
            board=board,
            turn=turn,
            castling_rights=castling_rights,
            en_passant_square=en_passant_square,
            halfmove_clock=halfmove_clock,
            fullmove_number=fullmove_number,
        )

    except FENParseError:
        raise
    except Exception as e:
        raise FENParseError(str(e), fen) from e


def _parse_board_part(board_part: str) -> list[Optional[Piece]]:
    """
    解析 FEN 棋盘部分
    Parse FEN board part

    Args:
        board_part: Board part of FEN string

    Returns:
        List of 64 squares (pieces or None)

    Raises:
        FENParseError: If board part is invalid
    """
    board = [None] * 64
    ranks = board_part.split("/")

    if len(ranks) != 8:
        raise FENParseError(f"Board must have 8 ranks, got {len(ranks)}")

    # FEN 从第 8 等级（黑方）开始 FEN starts from rank 8 (black's side)
    for rank_idx, rank_str in enumerate(ranks):
        file_idx = 0
        for char in rank_str:
            if char.isdigit():
                # 空格数 Number of empty squares
                empty_count = int(char)
                if empty_count < 1 or empty_count > 8:
                    raise FENParseError(f"Invalid empty square count: {char}")
                file_idx += empty_count
            else:
                # 棋子 Piece
                try:
                    piece = Piece.from_symbol(char)
                except ValueError:
                    raise FENParseError(f"Invalid piece symbol: {char}")

                if file_idx >= 8:
                    raise FENParseError(f"Too many pieces in rank {8 - rank_idx}")

                # 转换为内部坐标系（第 0 等级 = 白方）
                # Convert to internal coordinate system (rank 0 = white's side)
                actual_rank = 7 - rank_idx
                square = Square(file=file_idx, rank=actual_rank)
                board[square.to_index()] = piece
                file_idx += 1

        if file_idx != 8:
            raise FENParseError(f"Rank {8 - rank_idx} has {file_idx} squares, expected 8")

    return board


def board_to_fen(state: BoardState) -> str:
    """
    将棋盘状态序列化为 FEN 字符串
    Serialize board state to FEN string

    Args:
        state: Board state

    Returns:
        FEN string
    """
    # 棋盘部分 Board part
    board_part = _board_to_fen_part(state)

    # 轮次 Turn
    turn_part = "w" if state.turn == Color.WHITE else "b"

    # 王车易位 Castling
    castling_part = state.castling_rights.to_fen()

    # 吃过路兵 En passant
    ep_part = state.en_passant_square.to_algebraic() if state.en_passant_square else "-"

    # 半回合计数 Halfmove clock
    halfmove_part = str(state.halfmove_clock)

    # 全回合数 Fullmove number
    fullmove_part = str(state.fullmove_number)

    return f"{board_part} {turn_part} {castling_part} {ep_part} {halfmove_part} {fullmove_part}"


def _board_to_fen_part(state: BoardState) -> str:
    """
    将棋盘转换为 FEN 棋盘部分
    Convert board to FEN board part

    Args:
        state: Board state

    Returns:
        Board part of FEN string
    """
    ranks = []

    # FEN 从第 8 等级（黑方）开始 FEN starts from rank 8 (black's side)
    for rank_idx in range(7, -1, -1):
        rank_str = ""
        empty_count = 0

        for file_idx in range(8):
            square = Square(file=file_idx, rank=rank_idx)
            piece = state.get_piece(square)

            if piece is None:
                empty_count += 1
            else:
                if empty_count > 0:
                    rank_str += str(empty_count)
                    empty_count = 0
                rank_str += piece.symbol()

        if empty_count > 0:
            rank_str += str(empty_count)

        ranks.append(rank_str)

    return "/".join(ranks)


def get_starting_position() -> BoardState:
    """
    获取起始棋盘位置
    Get starting board position

    Returns:
        BoardState with starting position
    """
    return parse_fen(STARTING_FEN)
