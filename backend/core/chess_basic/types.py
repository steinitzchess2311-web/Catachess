"""
chess_basic.types
BoardState、Move、Color 等基础类型定义

Core type definitions for chess game representation.
"""

from dataclasses import dataclass, field
from typing import Optional
from .constants import Color, PieceType, CastlingRight


@dataclass(frozen=True)
class Square:
    """
    棋盘格子 Chess board square

    Represents a square on the chess board using file (column) and rank (row).
    Immutable.
    """
    file: int  # 0-7, a-h
    rank: int  # 0-7, 1-8

    def __post_init__(self):
        if not (0 <= self.file < 8):
            raise ValueError(f"Invalid file: {self.file}")
        if not (0 <= self.rank < 8):
            raise ValueError(f"Invalid rank: {self.rank}")

    def to_index(self) -> int:
        """转换为 0-63 索引 Convert to 0-63 index"""
        return self.rank * 8 + self.file

    @classmethod
    def from_index(cls, index: int) -> "Square":
        """从 0-63 索引创建 Create from 0-63 index"""
        if not (0 <= index < 64):
            raise ValueError(f"Invalid square index: {index}")
        return cls(file=index % 8, rank=index // 8)

    def to_algebraic(self) -> str:
        """转换为代数记法 e.g., 'e4' Convert to algebraic notation"""
        return chr(ord('a') + self.file) + str(self.rank + 1)

    @classmethod
    def from_algebraic(cls, notation: str) -> "Square":
        """从代数记法创建 e.g., 'e4' Create from algebraic notation"""
        if len(notation) != 2:
            raise ValueError(f"Invalid algebraic notation: {notation}")
        file = ord(notation[0].lower()) - ord('a')
        rank = int(notation[1]) - 1
        return cls(file=file, rank=rank)


@dataclass(frozen=True)
class Piece:
    """
    棋子 Chess piece

    Represents a chess piece with color and type. Immutable.
    """
    color: Color
    piece_type: PieceType

    def symbol(self) -> str:
        """返回棋子符号（白棋大写，黑棋小写）Return piece symbol (uppercase for white, lowercase for black)"""
        from .constants import PIECE_SYMBOLS
        symbol = PIECE_SYMBOLS[self.piece_type]
        return symbol.upper() if self.color == Color.WHITE else symbol

    def unicode_symbol(self) -> str:
        """返回 Unicode 棋子符号 Return Unicode piece symbol"""
        from .constants import UNICODE_PIECES
        return UNICODE_PIECES[(self.color, self.piece_type)]

    @classmethod
    def from_symbol(cls, symbol: str) -> "Piece":
        """从符号创建棋子 Create piece from symbol"""
        from .constants import PIECE_SYMBOLS
        color = Color.WHITE if symbol.isupper() else Color.BLACK
        symbol_lower = symbol.lower()

        for piece_type, piece_symbol in PIECE_SYMBOLS.items():
            if piece_symbol == symbol_lower:
                return cls(color=color, piece_type=piece_type)

        raise ValueError(f"Invalid piece symbol: {symbol}")


@dataclass(frozen=True)
class Move:
    """
    走法 Chess move

    Represents a move from one square to another, with optional promotion.
    Immutable.
    """
    from_square: Square
    to_square: Square
    promotion: Optional[PieceType] = None  # 升变棋子类型 Promotion piece type

    def to_uci(self) -> str:
        """转换为 UCI 格式 e.g., 'e2e4', 'e7e8q' Convert to UCI format"""
        uci = self.from_square.to_algebraic() + self.to_square.to_algebraic()
        if self.promotion:
            from .constants import PIECE_SYMBOLS
            uci += PIECE_SYMBOLS[self.promotion]
        return uci

    @classmethod
    def from_uci(cls, uci: str) -> "Move":
        """从 UCI 格式创建走法 Create move from UCI format"""
        if len(uci) < 4:
            raise ValueError(f"Invalid UCI move: {uci}")

        from_square = Square.from_algebraic(uci[:2])
        to_square = Square.from_algebraic(uci[2:4])

        promotion = None
        if len(uci) == 5:
            from .constants import PIECE_SYMBOLS
            promotion_char = uci[4].lower()
            for piece_type, symbol in PIECE_SYMBOLS.items():
                if symbol == promotion_char:
                    promotion = piece_type
                    break
            if promotion is None:
                raise ValueError(f"Invalid promotion piece: {uci[4]}")

        return cls(from_square=from_square, to_square=to_square, promotion=promotion)


@dataclass
class CastlingRights:
    """
    王车易位权利 Castling rights

    Tracks which castling moves are still available.
    """
    white_kingside: bool = True
    white_queenside: bool = True
    black_kingside: bool = True
    black_queenside: bool = True

    def has_right(self, right: CastlingRight) -> bool:
        """检查是否有特定王车易位权利 Check if specific castling right exists"""
        if right == CastlingRight.WHITE_KINGSIDE:
            return self.white_kingside
        elif right == CastlingRight.WHITE_QUEENSIDE:
            return self.white_queenside
        elif right == CastlingRight.BLACK_KINGSIDE:
            return self.black_kingside
        elif right == CastlingRight.BLACK_QUEENSIDE:
            return self.black_queenside
        return False

    def remove_right(self, right: CastlingRight) -> None:
        """移除特定王车易位权利 Remove specific castling right"""
        if right == CastlingRight.WHITE_KINGSIDE:
            self.white_kingside = False
        elif right == CastlingRight.WHITE_QUEENSIDE:
            self.white_queenside = False
        elif right == CastlingRight.BLACK_KINGSIDE:
            self.black_kingside = False
        elif right == CastlingRight.BLACK_QUEENSIDE:
            self.black_queenside = False

    def to_fen(self) -> str:
        """转换为 FEN 格式 Convert to FEN format"""
        fen = ""
        if self.white_kingside:
            fen += "K"
        if self.white_queenside:
            fen += "Q"
        if self.black_kingside:
            fen += "k"
        if self.black_queenside:
            fen += "q"
        return fen if fen else "-"

    @classmethod
    def from_fen(cls, fen: str) -> "CastlingRights":
        """从 FEN 格式创建 Create from FEN format"""
        if fen == "-":
            return cls(False, False, False, False)

        return cls(
            white_kingside="K" in fen,
            white_queenside="Q" in fen,
            black_kingside="k" in fen,
            black_queenside="q" in fen,
        )


@dataclass
class BoardState:
    """
    棋盘状态 Board state

    Complete representation of the current board position including:
    - Piece placement
    - Turn to move
    - Castling rights
    - En passant target
    - Halfmove clock (for 50-move rule)
    - Fullmove number
    """
    # 棋盘表示：64 个格子，每个格子可能有棋子或为空
    # Board representation: 64 squares, each may contain a piece or be empty
    board: list[Optional[Piece]] = field(default_factory=lambda: [None] * 64)

    # 当前轮到谁走 Current turn
    turn: Color = Color.WHITE

    # 王车易位权利 Castling rights
    castling_rights: CastlingRights = field(default_factory=CastlingRights)

    # 吃过路兵目标格 En passant target square (if applicable)
    en_passant_square: Optional[Square] = None

    # 半回合计数（用于 50 回合规则）Halfmove clock for 50-move rule
    halfmove_clock: int = 0

    # 全回合数 Fullmove number (starts at 1, increments after Black's move)
    fullmove_number: int = 1

    def get_piece(self, square: Square) -> Optional[Piece]:
        """获取指定格子的棋子 Get piece at square"""
        return self.board[square.to_index()]

    def set_piece(self, square: Square, piece: Optional[Piece]) -> None:
        """在指定格子放置棋子 Set piece at square"""
        self.board[square.to_index()] = piece

    def copy(self) -> "BoardState":
        """创建棋盘状态的深拷贝 Create deep copy of board state"""
        from copy import deepcopy
        return deepcopy(self)
