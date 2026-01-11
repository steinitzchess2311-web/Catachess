"""
chess_basic.constants
棋盘尺寸、棋子编码、颜色等常量

Core constants for chess game representation.
"""

from enum import IntEnum, Enum
from typing import Final

# 棋盘尺寸 Board dimensions
BOARD_SIZE: Final[int] = 8
NUM_SQUARES: Final[int] = 64

# 文件（列）Files (columns)
FILES: Final[str] = "abcdefgh"
# 等级（行）Ranks (rows)
RANKS: Final[str] = "12345678"


class Color(IntEnum):
    """棋子颜色 Piece colors"""
    WHITE = 0
    BLACK = 1

    def opposite(self) -> "Color":
        """返回相反颜色 Return opposite color"""
        return Color.BLACK if self == Color.WHITE else Color.WHITE


class PieceType(IntEnum):
    """棋子类型 Piece types (without color)"""
    PAWN = 1
    KNIGHT = 2
    BISHOP = 3
    ROOK = 4
    QUEEN = 5
    KING = 6


# 棋子字符表示 Piece character representation
PIECE_SYMBOLS: Final[dict[PieceType, str]] = {
    PieceType.PAWN: "p",
    PieceType.KNIGHT: "n",
    PieceType.BISHOP: "b",
    PieceType.ROOK: "r",
    PieceType.QUEEN: "q",
    PieceType.KING: "k",
}

# Unicode 棋子符号 Unicode piece symbols for display
UNICODE_PIECES: Final[dict[tuple[Color, PieceType], str]] = {
    (Color.WHITE, PieceType.KING): "♔",
    (Color.WHITE, PieceType.QUEEN): "♕",
    (Color.WHITE, PieceType.ROOK): "♖",
    (Color.WHITE, PieceType.BISHOP): "♗",
    (Color.WHITE, PieceType.KNIGHT): "♘",
    (Color.WHITE, PieceType.PAWN): "♙",
    (Color.BLACK, PieceType.KING): "♚",
    (Color.BLACK, PieceType.QUEEN): "♛",
    (Color.BLACK, PieceType.ROOK): "♜",
    (Color.BLACK, PieceType.BISHOP): "♝",
    (Color.BLACK, PieceType.KNIGHT): "♞",
    (Color.BLACK, PieceType.PAWN): "♟",
}

# 起始 FEN Starting position FEN
STARTING_FEN: Final[str] = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

# 王车易位类型 Castling types
class CastlingRight(IntEnum):
    """王车易位权利 Castling rights"""
    WHITE_KINGSIDE = 0   # K
    WHITE_QUEENSIDE = 1  # Q
    BLACK_KINGSIDE = 2   # k
    BLACK_QUEENSIDE = 3  # q


# 王车易位 FEN 字符 Castling FEN characters
CASTLING_CHARS: Final[dict[CastlingRight, str]] = {
    CastlingRight.WHITE_KINGSIDE: "K",
    CastlingRight.WHITE_QUEENSIDE: "Q",
    CastlingRight.BLACK_KINGSIDE: "k",
    CastlingRight.BLACK_QUEENSIDE: "q",
}

# 游戏结果 Game results
class GameResult(Enum):
    """对局结果 Game result"""
    IN_PROGRESS = "*"
    WHITE_WINS = "1-0"
    BLACK_WINS = "0-1"
    DRAW = "1/2-1/2"


# 游戏终止原因 Game termination reasons
class TerminationReason(Enum):
    """终止原因 Termination reason"""
    CHECKMATE = "checkmate"
    STALEMATE = "stalemate"
    INSUFFICIENT_MATERIAL = "insufficient_material"
    FIFTY_MOVE_RULE = "fifty_move_rule"
    THREEFOLD_REPETITION = "threefold_repetition"
    RESIGNATION = "resignation"
    TIMEOUT = "timeout"
    AGREEMENT = "agreement"
