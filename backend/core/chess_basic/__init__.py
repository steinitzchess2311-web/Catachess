"""
chess_basic 模块入口

Core chess engine module providing:
- Basic chess constants and types
- Rule validation and move generation
- PGN recording (with and without variations)
- Utility functions for chess notation

This module is the foundation of the chess engine and operates
independently of UI, networking, or user management.
"""

from .constants import *
from .types import *
from .errors import *

__all__ = [
    # Re-export from submodules will be added as they're implemented
]
