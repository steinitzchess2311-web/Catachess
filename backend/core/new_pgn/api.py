"""
Public API for PGN detection.
"""
from .types import PGNGame
from .normalize import normalize_pgn
from .detector import split_games


def detect_games(pgn_text: str) -> list[PGNGame]:
    """
    Detect individual PGN games in a multi-game PGN string.

    This is the main entry point for the new PGN pipeline.
    It normalizes input and splits it into individual games.

    Args:
        pgn_text: Raw PGN string (may contain multiple games).

    Returns:
        List of PGNGame objects, one per detected game.
        Returns empty list if no valid games (with headers) are found.
    """
    normalized = normalize_pgn(pgn_text)
    return split_games(normalized)
