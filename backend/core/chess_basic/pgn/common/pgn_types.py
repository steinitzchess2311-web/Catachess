"""
chess_basic.pgn.common.pgn_types
PGN 相关数据结构定义

PGN data structure definitions.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PGNMove:
    """
    PGN 中的单个走法
    Single move in PGN

    Attributes:
        san: Standard Algebraic Notation
        comment: Optional comment after the move
        nags: Numeric Annotation Glyphs (e.g., !, ?, !!, ??, !?, ?!)
    """
    san: str
    comment: Optional[str] = None
    nags: list[int] = field(default_factory=list)


@dataclass
class PGNNode:
    """
    PGN 游戏树节点
    PGN game tree node

    Attributes:
        move: Move at this node
        variations: Alternative variations from this position
        comment_before: Comment before the move
    """
    move: PGNMove
    variations: list["PGNNode"] = field(default_factory=list)
    comment_before: Optional[str] = None


@dataclass
class PGNGame:
    """
    完整的 PGN 对局
    Complete PGN game

    Attributes:
        tags: Game metadata tags
        moves: Main line moves (or root of game tree for variations)
        result: Game result (1-0, 0-1, 1/2-1/2, *)
    """
    tags: dict[str, str] = field(default_factory=dict)
    moves: list[PGNNode] = field(default_factory=list)
    result: str = "*"


# NAG (Numeric Annotation Glyph) 常量
# NAG (Numeric Annotation Glyph) constants
NAG_GOOD_MOVE = 1          # !
NAG_MISTAKE = 2            # ?
NAG_BRILLIANT_MOVE = 3     # !!
NAG_BLUNDER = 4            # ??
NAG_INTERESTING_MOVE = 5   # !?
NAG_DUBIOUS_MOVE = 6       # ?!

NAG_SYMBOLS = {
    1: "!",
    2: "?",
    3: "!!",
    4: "??",
    5: "!?",
    6: "?!",
}

NAG_FROM_SYMBOL = {v: k for k, v in NAG_SYMBOLS.items()}
