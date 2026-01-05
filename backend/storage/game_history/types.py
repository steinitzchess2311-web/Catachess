"""
Game History Types - Data Transfer Objects

Purpose:
    Define pure data structures for the game history domain.
    These are NOT:
    - ORM models (those are in models/)
    - API schemas (those are in routers/)
    - Database tables

    These ARE:
    - Data containers for storage operations
    - DTOs (Data Transfer Objects) for internal use
    - Type hints for better IDE support

Key Principle:
    These types exist in the "storage domain" and represent
    data as it relates to storage, not the database or API.
"""
from typing import TypedDict
from datetime import datetime


class GameMeta(TypedDict):
    """
    Metadata for a game.

    This represents the minimal information needed to identify and
    describe a game in the storage system.

    Attributes:
        game_id: Unique identifier for the game
        created_at: When the game was created
        white_player: White player identifier (optional)
        black_player: Black player identifier (optional)
        result: Game result (e.g., "1-0", "0-1", "1/2-1/2", None for ongoing)
        event: Event/assignment name (optional)

    Example:
        >>> meta: GameMeta = {
        ...     "game_id": "8f2a9c",
        ...     "created_at": datetime.now(),
        ...     "result": "1-0",
        ... }
    """
    game_id: str
    created_at: datetime
    white_player: str | None
    black_player: str | None
    result: str | None
    event: str | None


class AnalysisMeta(TypedDict):
    """
    Metadata for game analysis.

    This represents information about an engine analysis result.

    Attributes:
        game_id: Game this analysis belongs to
        engine_version: Engine version used
        depth: Analysis depth
        analyzed_at: When analysis was performed
        move_count: Number of moves analyzed

    Example:
        >>> analysis: AnalysisMeta = {
        ...     "game_id": "8f2a9c",
        ...     "engine_version": "Stockfish 16",
        ...     "depth": 20,
        ...     "analyzed_at": datetime.now(),
        ...     "move_count": 45,
        ... }
    """
    game_id: str
    engine_version: str
    depth: int
    analyzed_at: datetime
    move_count: int


class StorageStats(TypedDict):
    """
    Storage statistics for a game.

    This represents size and storage metadata.

    Attributes:
        game_id: Game identifier
        pgn_size_bytes: Size of PGN file in bytes
        analysis_size_bytes: Size of analysis file in bytes (if exists)
        total_size_bytes: Total storage used

    Example:
        >>> stats: StorageStats = {
        ...     "game_id": "8f2a9c",
        ...     "pgn_size_bytes": 1024,
        ...     "analysis_size_bytes": 2048,
        ...     "total_size_bytes": 3072,
        ... }
    """
    game_id: str
    pgn_size_bytes: int
    analysis_size_bytes: int | None
    total_size_bytes: int
