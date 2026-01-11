"""Database session management."""

from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from workspace.db.base import Base
class DatabaseConfig:
    """Database configuration."""

    def __init__(self, database_url: str, echo: bool = False) -> None:
        """Initialize database configuration."""
        self.database_url = database_url
        self.echo = echo
        self._schema_ready = False
        self._auto_create_schema = "sqlite" in database_url

        is_sqlite = "sqlite" in database_url
        connect_args: dict[str, Any] | None = None
        if is_sqlite:
            connect_args = {"check_same_thread": False}

        # Create async engine
        self.engine = create_async_engine(
            database_url,
            echo=echo,
            poolclass=StaticPool if is_sqlite else None,
            connect_args=connect_args,
        )

        # Create session factory
        self.async_session_maker = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

# Global database config (will be initialized by application)
_db_config: DatabaseConfig | None = None

def init_db(database_url: str, echo: bool = False) -> DatabaseConfig:
    """Initialize global database configuration."""
    global _db_config
    _db_config = DatabaseConfig(database_url, echo)
    return _db_config

def get_db_config() -> DatabaseConfig:
    """Get global database configuration."""
    if _db_config is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _db_config

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency injection helper for FastAPI."""
    config = get_db_config()
    if config._auto_create_schema and not config._schema_ready:
        import workspace.db.tables  # noqa: F401
        async with config.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        config._schema_ready = True
    async with config.async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
