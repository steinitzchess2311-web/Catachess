"""
chess_basic.pgn
PGN 模块入口

PGN (Portable Game Notation) recording module.

This module provides PGN writing functionality with two modes:
- no_vari: Simple mainline-only PGN writer
- vari: Full PGN writer with variation support
"""

from .common.pgn_types import *
from .common.tags import *

__all__ = [
    # PGN types
    "PGNGame",
    "PGNNode",
    "PGNMove",

    # Tags
    "PGNTags",
    "SevenTagRoster",
]
