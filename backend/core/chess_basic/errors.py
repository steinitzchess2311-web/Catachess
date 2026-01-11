"""
chess_basic.errors
非法走法、解析失败等核心异常

Core exceptions for the chess engine.
"""


class ChessError(Exception):
    """所有国际象棋相关错误的基类 Base class for all chess-related errors"""
    pass


class IllegalMoveError(ChessError):
    """非法走法错误 Raised when attempting an illegal move"""

    def __init__(self, message: str, move: str | None = None):
        self.move = move
        super().__init__(f"Illegal move{f' {move}' if move else ''}: {message}")


class InvalidPositionError(ChessError):
    """无效棋盘位置错误 Raised when the board position is invalid"""
    pass


class FENParseError(ChessError):
    """FEN 解析错误 Raised when FEN string cannot be parsed"""

    def __init__(self, message: str, fen: str | None = None):
        self.fen = fen
        super().__init__(f"FEN parse error{f' for {fen}' if fen else ''}: {message}")


class UCIParseError(ChessError):
    """UCI 走法解析错误 Raised when UCI move string cannot be parsed"""

    def __init__(self, message: str, uci: str | None = None):
        self.uci = uci
        super().__init__(f"UCI parse error{f' for {uci}' if uci else ''}: {message}")


class SANParseError(ChessError):
    """SAN 表示法解析错误 Raised when SAN move string cannot be parsed"""

    def __init__(self, message: str, san: str | None = None):
        self.san = san
        super().__init__(f"SAN parse error{f' for {san}' if san else ''}: {message}")


class AmbiguousMoveError(ChessError):
    """模糊走法错误 Raised when a move notation is ambiguous"""
    pass


class KingInCheckError(IllegalMoveError):
    """王被将军错误 Raised when move leaves or puts own king in check"""

    def __init__(self, move: str | None = None):
        super().__init__("Move leaves king in check", move)


class InvalidSquareError(ChessError):
    """无效格子错误 Raised when square coordinate is invalid"""

    def __init__(self, square: str | int):
        self.square = square
        super().__init__(f"Invalid square: {square}")


class PGNError(ChessError):
    """PGN 相关错误基类 Base class for PGN-related errors"""
    pass


class PGNParseError(PGNError):
    """PGN 解析错误 Raised when PGN cannot be parsed"""
    pass


class PGNWriteError(PGNError):
    """PGN 写入错误 Raised when PGN cannot be written"""
    pass


class InvalidVariationError(PGNError):
    """无效分支错误 Raised when variation structure is invalid"""
    pass
