"""
chess_basic.rule
规则模块入口

Rule engine module for chess move generation and validation.
"""

from .api import *

__all__ = [
    "is_legal_move",
    "apply_move",
    "generate_legal_moves",
    "is_check",
    "is_checkmate",
    "is_stalemate",
    "is_game_over",
    "get_game_result",
]
