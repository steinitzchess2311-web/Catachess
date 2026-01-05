"""
Game History Store - Content Storage Operations

Purpose:
    Handle storage and retrieval of game content (PGN, analysis JSON).
    This module manages CONTENT, not PERMISSIONS or OWNERSHIP.

Key Principle:
    This module:
    ✓ Knows what a PGN is
    ✓ Knows what analysis JSON is
    ✓ Knows how to serialize/deserialize them

    But does NOT know:
    ✗ Who owns the game
    ✗ Who can access it
    ✗ Which games to list for a user

    Those concerns are handled by the index layer.

Why this separation matters:
    - Storage operations can be tested independently
    - Permission logic can change without touching storage
    - Easy to add new content types (training data, thumbnails)
    - Clear responsibility boundaries
"""
import json
from typing import Any

from storage.core.client import StorageClient
from storage.core.config import StorageConfig
from storage.core.errors import ObjectNotFound
from storage.game_history.keys import game_pgn, game_analysis


# Module-level client instance (initialized lazily)
_storage_client: StorageClient | None = None


def get_storage_client() -> StorageClient:
    """
    Get or create the storage client instance.

    This uses lazy initialization to avoid requiring R2 credentials
    during import.

    Returns:
        StorageClient instance

    Raises:
        ValueError: If R2 environment variables are not set
    """
    global _storage_client
    if _storage_client is None:
        config = StorageConfig.from_env()
        _storage_client = StorageClient(config)
    return _storage_client


def save_pgn(game_id: str, pgn_content: str) -> None:
    """
    Save PGN content for a game.

    This stores the raw PGN text in R2. It does NOT:
    - Validate the PGN format
    - Check permissions
    - Update any database

    Args:
        game_id: Unique game identifier
        pgn_content: PGN text content

    Raises:
        StorageUnavailable: If R2 is unreachable
        StorageError: For other storage errors

    Example:
        >>> pgn = '''[Event "Casual Game"]
        ... [Site "Chess.com"]
        ... [Date "2024.01.05"]
        ... [White "Player1"]
        ... [Black "Player2"]
        ... [Result "1-0"]
        ...
        ... 1. e4 e5 2. Nf3 Nc6 3. Bb5 1-0'''
        >>> save_pgn("8f2a9c", pgn)
    """
    client = get_storage_client()
    key = game_pgn(game_id)

    # Convert string to bytes with UTF-8 encoding
    content_bytes = pgn_content.encode("utf-8")

    # Store with appropriate content type
    client.put_object(
        key=key,
        content=content_bytes,
        content_type="application/x-chess-pgn"
    )


def load_pgn(game_id: str) -> str:
    """
    Load PGN content for a game.

    Args:
        game_id: Unique game identifier

    Returns:
        PGN text content

    Raises:
        ObjectNotFound: If game PGN doesn't exist
        StorageUnavailable: If R2 is unreachable
        StorageError: For other storage errors

    Example:
        >>> pgn = load_pgn("8f2a9c")
        >>> print(pgn)
        [Event "Casual Game"]
        [Site "Chess.com"]
        ...
    """
    client = get_storage_client()
    key = game_pgn(game_id)

    # Get bytes and decode to string
    content_bytes = client.get_object(key)
    return content_bytes.decode("utf-8")


def pgn_exists(game_id: str) -> bool:
    """
    Check if PGN exists for a game.

    Args:
        game_id: Unique game identifier

    Returns:
        True if PGN exists, False otherwise

    Example:
        >>> save_pgn("8f2a9c", "[Event \"Test\"]")
        >>> pgn_exists("8f2a9c")
        True
        >>> pgn_exists("nonexistent")
        False
    """
    client = get_storage_client()
    key = game_pgn(game_id)
    return client.exists(key)


def delete_pgn(game_id: str) -> None:
    """
    Delete PGN for a game.

    This is idempotent - deleting a non-existent PGN succeeds.

    Args:
        game_id: Unique game identifier

    Raises:
        StorageUnavailable: If R2 is unreachable
        StorageError: For other storage errors

    Example:
        >>> delete_pgn("8f2a9c")
        >>> # No error even if already deleted
        >>> delete_pgn("8f2a9c")
    """
    client = get_storage_client()
    key = game_pgn(game_id)
    client.delete_object(key)


def save_analysis(game_id: str, analysis_data: dict[str, Any]) -> None:
    """
    Save analysis data for a game.

    The analysis data is stored as JSON. The structure is flexible,
    but typically contains:
    - moves: List of moves with evaluations
    - best_moves: Engine's suggested best moves
    - blunders: Detected mistakes
    - statistics: Position statistics

    Args:
        game_id: Unique game identifier
        analysis_data: Analysis data dictionary

    Raises:
        StorageUnavailable: If R2 is unreachable
        StorageError: For other storage errors

    Example:
        >>> analysis = {
        ...     "moves": [
        ...         {"move": "e4", "eval": 0.3, "best": True},
        ...         {"move": "e5", "eval": 0.2, "best": True},
        ...     ],
        ...     "blunders": [],
        ... }
        >>> save_analysis("8f2a9c", analysis)
    """
    client = get_storage_client()
    key = game_analysis(game_id)

    # Serialize to JSON and encode
    json_str = json.dumps(analysis_data, indent=2)
    content_bytes = json_str.encode("utf-8")

    client.put_object(
        key=key,
        content=content_bytes,
        content_type="application/json"
    )


def load_analysis(game_id: str) -> dict[str, Any]:
    """
    Load analysis data for a game.

    Args:
        game_id: Unique game identifier

    Returns:
        Analysis data dictionary

    Raises:
        ObjectNotFound: If analysis doesn't exist
        StorageUnavailable: If R2 is unreachable
        StorageError: For other storage errors
        json.JSONDecodeError: If stored JSON is invalid

    Example:
        >>> analysis = load_analysis("8f2a9c")
        >>> print(analysis["moves"][0])
        {'move': 'e4', 'eval': 0.3, 'best': True}
    """
    client = get_storage_client()
    key = game_analysis(game_id)

    # Get bytes, decode, and parse JSON
    content_bytes = client.get_object(key)
    json_str = content_bytes.decode("utf-8")
    return json.loads(json_str)


def analysis_exists(game_id: str) -> bool:
    """
    Check if analysis exists for a game.

    Args:
        game_id: Unique game identifier

    Returns:
        True if analysis exists, False otherwise

    Example:
        >>> save_analysis("8f2a9c", {"moves": []})
        >>> analysis_exists("8f2a9c")
        True
        >>> analysis_exists("nonexistent")
        False
    """
    client = get_storage_client()
    key = game_analysis(game_id)
    return client.exists(key)


def delete_analysis(game_id: str) -> None:
    """
    Delete analysis for a game.

    This is idempotent - deleting non-existent analysis succeeds.

    Args:
        game_id: Unique game identifier

    Raises:
        StorageUnavailable: If R2 is unreachable
        StorageError: For other storage errors

    Example:
        >>> delete_analysis("8f2a9c")
    """
    client = get_storage_client()
    key = game_analysis(game_id)
    client.delete_object(key)


def delete_game_content(game_id: str) -> None:
    """
    Delete all content for a game (PGN and analysis).

    This is a convenience function that deletes both PGN and analysis.
    It's idempotent - deleting non-existent content succeeds.

    Args:
        game_id: Unique game identifier

    Raises:
        StorageUnavailable: If R2 is unreachable
        StorageError: For other storage errors

    Example:
        >>> delete_game_content("8f2a9c")
    """
    delete_pgn(game_id)
    delete_analysis(game_id)
