"""
Game History Index - Protocol Definition

Purpose:
    Define the interface for game history indexing WITHOUT implementing it.
    This is one of the most important architectural decisions in the system.

Why this exists:
    The index answers: "Which games can this user see?"
    The store answers: "What is the content of this game?"

    By separating these concerns, we can:
    - Change how we index (Postgres, R2 JSON, Redis, etc.)
    - Change visibility rules without touching storage
    - Test index and store independently
    - Scale index and store separately

Key Principle:
    This file defines WHAT the index must do, not HOW it does it.

    ✓ Protocol: Interface contract
    ✗ Implementation: Actual code that works

Why Protocol instead of ABC:
    - Runtime duck typing (more Pythonic)
    - No inheritance required
    - Easy to mock in tests
    - Clear separation of interface from implementation

Future Implementations (you pick later):
    1. PostgresGameIndex: Use database (recommended for production)
    2. R2JsonIndex: Use R2 for everything (simple, but slower queries)
    3. RedisGameIndex: Use Redis (fast, but more infrastructure)
    4. HybridIndex: Postgres + Redis cache

For now, this file just defines what an index MUST be able to do.
"""
from typing import Protocol, List
from datetime import datetime

from storage.game_history.types import GameMeta


class GameHistoryIndex(Protocol):
    """
    Protocol for game history indexing.

    Any class that implements these methods can be used as a game history index.
    This allows the rest of the system to work with any indexing strategy.

    The index is responsible for:
    - Tracking which games exist
    - Tracking who can see which games
    - Providing metadata for listing/searching
    - NOT storing the actual game content (that's storage/game_history/store)

    Example implementations (none exist yet):
        >>> # Future Postgres implementation
        >>> class PostgresGameIndex:
        ...     def add_game(self, user_id, game_id, created_at):
        ...         db.execute("INSERT INTO game_index ...")
        ...     def list_games(self, user_id):
        ...         return db.query("SELECT ... WHERE user_id = ...")
        ...
        >>> # Future R2 JSON implementation
        >>> class R2JsonIndex:
        ...     def add_game(self, user_id, game_id, created_at):
        ...         # Update users/{user_id}/games.json in R2
        ...     def list_games(self, user_id):
        ...         # Read users/{user_id}/games.json from R2
    """

    def add_game(
        self,
        user_id: str,
        game_id: str,
        created_at: datetime,
        white_player: str | None = None,
        black_player: str | None = None,
        result: str | None = None,
        event: str | None = None,
    ) -> None:
        """
        Add a game to the user's visible games.

        This creates an index entry that allows the user to see this game.
        It does NOT store the game content (that's store.save_pgn).

        Args:
            user_id: User who can see this game
            game_id: Unique game identifier
            created_at: When the game was created
            white_player: White player identifier (optional)
            black_player: Black player identifier (optional)
            result: Game result (e.g., "1-0", "0-1", "1/2-1/2")
            event: Event/assignment name (optional)

        Raises:
            IndexError: If indexing fails

        Example:
            >>> index.add_game(
            ...     user_id="user_123",
            ...     game_id="game_8f2a9c",
            ...     created_at=datetime.now(),
            ...     result="1-0"
            ... )
        """
        ...

    def list_games(
        self,
        user_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> List[GameMeta]:
        """
        List games visible to a user.

        This returns metadata only, not the actual game content.
        To get content, use store.load_pgn(game_id).

        Args:
            user_id: User whose games to list
            limit: Maximum number of games to return
            offset: Number of games to skip (for pagination)

        Returns:
            List of GameMeta objects (newest first)

        Raises:
            IndexError: If query fails

        Example:
            >>> games = index.list_games("user_123", limit=10)
            >>> for game in games:
            ...     print(f"{game['game_id']}: {game['result']}")
            game_8f2a9c: 1-0
            game_71caa2: 0-1
        """
        ...

    def get_game(
        self,
        user_id: str,
        game_id: str,
    ) -> GameMeta | None:
        """
        Get metadata for a specific game if user can see it.

        Args:
            user_id: User requesting the game
            game_id: Game to get metadata for

        Returns:
            GameMeta if user can see the game, None otherwise

        Example:
            >>> meta = index.get_game("user_123", "game_8f2a9c")
            >>> if meta:
            ...     print(f"Game {meta['game_id']} result: {meta['result']}")
            Game game_8f2a9c result: 1-0
        """
        ...

    def remove_game(
        self,
        user_id: str,
        game_id: str,
    ) -> None:
        """
        Remove a game from user's visible games.

        This removes the index entry. It does NOT delete the game content.
        To delete content, use store.delete_game_content(game_id).

        Args:
            user_id: User whose index to update
            game_id: Game to remove

        Raises:
            IndexError: If removal fails

        Example:
            >>> index.remove_game("user_123", "game_8f2a9c")
        """
        ...

    def game_exists_for_user(
        self,
        user_id: str,
        game_id: str,
    ) -> bool:
        """
        Check if a user can see a specific game.

        This is faster than get_game() when you only need existence check.

        Args:
            user_id: User to check
            game_id: Game to check

        Returns:
            True if user can see the game, False otherwise

        Example:
            >>> if index.game_exists_for_user("user_123", "game_8f2a9c"):
            ...     pgn = store.load_pgn("game_8f2a9c")
        """
        ...


# Type alias for convenience
GameIndex = GameHistoryIndex


# Note about implementation:
# This Protocol is NOT implemented yet. That's intentional.
# When you need to implement it, create a new file like:
#   storage/game_history/postgres_index.py
# or
#   storage/game_history/r2_index.py
#
# The implementation will import this Protocol and satisfy it.
