"""
Initialize game tables if they don't exist.
"""
from core.db.db_engine import db_engine
from core.db.base import Base

# Ensure models are registered with Base.metadata
from models.game import Game  # noqa: F401
from models.game_action import GameAction  # noqa: F401
from models.user import User  # noqa: F401


def init_game_tables() -> bool:
    """
    Create games and game_actions tables if they don't exist.

    Returns:
        True if tables were created/verified, False otherwise.
    """
    try:
        Base.metadata.create_all(
            bind=db_engine,
            tables=[Game.__table__, GameAction.__table__],
        )
        print("✓ game tables initialized successfully")
        return True
    except Exception as exc:
        print(f"✗ Failed to initialize game tables: {exc}")
        return False


if __name__ == "__main__":
    init_game_tables()
