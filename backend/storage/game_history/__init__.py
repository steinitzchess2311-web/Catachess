"""
Game History Storage - Content Domain

This module handles storage and retrieval of game history content (PGN, analysis).
It is a "content domain" - it manages what goes into storage, but not who can see it.

Key Principle:
    This module knows about:
    ✓ Game IDs
    ✓ PGN format
    ✓ Analysis JSON

    But NOT about:
    ✗ User IDs
    ✗ Permissions
    ✗ Who owns what

Exports:
    - save_pgn/load_pgn: Store and retrieve PGN content
    - GameMeta: Data transfer object for game metadata
    - GameHistoryIndex: Protocol for indexing (interface only)
"""
from storage.game_history.store import save_pgn, load_pgn, save_analysis, load_analysis
from storage.game_history.types import GameMeta
from storage.game_history.index import GameHistoryIndex

__all__ = [
    "save_pgn",
    "load_pgn",
    "save_analysis",
    "load_analysis",
    "GameMeta",
    "GameHistoryIndex",
]
