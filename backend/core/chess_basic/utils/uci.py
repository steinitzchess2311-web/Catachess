"""
chess_basic.utils.uci
UCI 走法解析与生成

UCI (Universal Chess Interface) move parsing and generation.
"""

from ..types import Move, Square
from ..constants import PieceType, PIECE_SYMBOLS
from ..errors import UCIParseError


def parse_uci_move(uci: str) -> Move:
    """
    解析 UCI 走法字符串
    Parse UCI move string

    Args:
        uci: UCI move string (e.g., 'e2e4', 'e7e8q')

    Returns:
        Move object

    Raises:
        UCIParseError: If UCI string is invalid
    """
    try:
        return Move.from_uci(uci)
    except ValueError as e:
        raise UCIParseError(str(e), uci) from e


def move_to_uci(move: Move) -> str:
    """
    将走法转换为 UCI 字符串
    Convert move to UCI string

    Args:
        move: Move object

    Returns:
        UCI move string (e.g., 'e2e4', 'e7e8q')
    """
    return move.to_uci()


def is_valid_uci_format(uci: str) -> bool:
    """
    检查字符串是否为有效的 UCI 格式（不检查走法是否合法）
    Check if string is valid UCI format (doesn't check if move is legal)

    Args:
        uci: Potential UCI move string

    Returns:
        True if format is valid, False otherwise
    """
    if len(uci) < 4 or len(uci) > 5:
        return False

    # 检查前 4 个字符是否为有效格子 Check if first 4 chars are valid squares
    try:
        from_notation = uci[:2]
        to_notation = uci[2:4]

        # 检查文件 Check files
        if from_notation[0] not in "abcdefgh" or to_notation[0] not in "abcdefgh":
            return False

        # 检查等级 Check ranks
        if from_notation[1] not in "12345678" or to_notation[1] not in "12345678":
            return False

        # 如果有第 5 个字符，检查是否为有效升变 If 5th char exists, check if valid promotion
        if len(uci) == 5:
            promotion_char = uci[4].lower()
            valid_promotions = {PIECE_SYMBOLS[pt] for pt in [
                PieceType.QUEEN, PieceType.ROOK, PieceType.BISHOP, PieceType.KNIGHT
            ]}
            if promotion_char not in valid_promotions:
                return False

        return True

    except Exception:
        return False


def uci_to_squares(uci: str) -> tuple[Square, Square]:
    """
    将 UCI 字符串转换为起始和目标格子
    Convert UCI string to from and to squares

    Args:
        uci: UCI move string

    Returns:
        Tuple of (from_square, to_square)

    Raises:
        UCIParseError: If UCI string is invalid
    """
    if len(uci) < 4:
        raise UCIParseError("UCI move must be at least 4 characters", uci)

    try:
        from_square = Square.from_algebraic(uci[:2])
        to_square = Square.from_algebraic(uci[2:4])
        return (from_square, to_square)
    except ValueError as e:
        raise UCIParseError(str(e), uci) from e
