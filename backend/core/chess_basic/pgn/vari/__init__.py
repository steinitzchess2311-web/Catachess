"""
chess_basic.pgn.vari
分支 PGN writer 模块入口

Variation-supporting PGN writer module.
"""

from .writer import *
from .variation_stack import *

__all__ = [
    "PGNWriterVari",
    "VariationStack",
]
