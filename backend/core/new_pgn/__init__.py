"""
New PGN pipeline.

Public API:
    detect_games: Detect individual games in a multi-game PGN string.
    PGNGame: Data class representing a single PGN game.
    PGNHeader: Type alias for header dictionary.
"""
from .api import detect_games
from .types import PGNGame, PGNHeader

__all__ = ["detect_games", "PGNGame", "PGNHeader"]
