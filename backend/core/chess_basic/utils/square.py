"""
chess_basic.utils.square
格子坐标与索引转换工具

Square coordinate and index conversion utilities.
"""

from ..types import Square
from ..errors import InvalidSquareError


def square_to_index(square: Square) -> int:
    """
    将格子转换为 0-63 索引
    Convert square to 0-63 index

    Args:
        square: Square object

    Returns:
        Index from 0-63
    """
    return square.to_index()


def index_to_square(index: int) -> Square:
    """
    将 0-63 索引转换为格子
    Convert 0-63 index to square

    Args:
        index: Index from 0-63

    Returns:
        Square object

    Raises:
        InvalidSquareError: If index is out of range
    """
    try:
        return Square.from_index(index)
    except ValueError as e:
        raise InvalidSquareError(index) from e


def algebraic_to_square(notation: str) -> Square:
    """
    将代数记法转换为格子 e.g., 'e4' -> Square
    Convert algebraic notation to square

    Args:
        notation: Algebraic notation (e.g., 'e4')

    Returns:
        Square object

    Raises:
        InvalidSquareError: If notation is invalid
    """
    try:
        return Square.from_algebraic(notation)
    except ValueError as e:
        raise InvalidSquareError(notation) from e


def square_to_algebraic(square: Square) -> str:
    """
    将格子转换为代数记法 e.g., Square -> 'e4'
    Convert square to algebraic notation

    Args:
        square: Square object

    Returns:
        Algebraic notation (e.g., 'e4')
    """
    return square.to_algebraic()


def is_valid_square(file: int, rank: int) -> bool:
    """
    检查文件和等级是否在有效范围内
    Check if file and rank are within valid range

    Args:
        file: File (column) 0-7
        rank: Rank (row) 0-7

    Returns:
        True if valid, False otherwise
    """
    return 0 <= file < 8 and 0 <= rank < 8


def distance(square1: Square, square2: Square) -> tuple[int, int]:
    """
    计算两个格子之间的距离（文件距离，等级距离）
    Calculate distance between two squares (file distance, rank distance)

    Args:
        square1: First square
        square2: Second square

    Returns:
        Tuple of (file_distance, rank_distance)
    """
    file_dist = abs(square1.file - square2.file)
    rank_dist = abs(square1.rank - square2.rank)
    return (file_dist, rank_dist)


def manhattan_distance(square1: Square, square2: Square) -> int:
    """
    计算两个格子之间的曼哈顿距离
    Calculate Manhattan distance between two squares

    Args:
        square1: First square
        square2: Second square

    Returns:
        Manhattan distance
    """
    file_dist, rank_dist = distance(square1, square2)
    return file_dist + rank_dist


def chebyshev_distance(square1: Square, square2: Square) -> int:
    """
    计算两个格子之间的切比雪夫距离（国王距离）
    Calculate Chebyshev distance (king distance) between two squares

    Args:
        square1: First square
        square2: Second square

    Returns:
        Chebyshev distance
    """
    file_dist, rank_dist = distance(square1, square2)
    return max(file_dist, rank_dist)


def is_diagonal(square1: Square, square2: Square) -> bool:
    """
    检查两个格子是否在对角线上
    Check if two squares are on a diagonal

    Args:
        square1: First square
        square2: Second square

    Returns:
        True if on diagonal, False otherwise
    """
    file_dist, rank_dist = distance(square1, square2)
    return file_dist == rank_dist and file_dist > 0


def is_orthogonal(square1: Square, square2: Square) -> bool:
    """
    检查两个格子是否在正交线上（同行或同列）
    Check if two squares are orthogonal (same rank or file)

    Args:
        square1: First square
        square2: Second square

    Returns:
        True if orthogonal, False otherwise
    """
    return (square1.file == square2.file or square1.rank == square2.rank) and square1 != square2
