"""Database session management."""

import asyncio
from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from modules.workspace.db.base import Base


class SchemaAwareSession(AsyncSession):
    def __init__(self, *args, **kwargs) -> None:
        self._db_config = kwargs.pop("_db_config", None)
        super().__init__(*args, **kwargs)

    async def __aenter__(self) -> "SchemaAwareSession":
        config = getattr(self, "_db_config", None)
        if config and config._auto_create_schema and (config._memory_db or not config._schema_ready):
            import modules.workspace.db.tables  # noqa: F401
            await _create_schema(config)
        return await super().__aenter__()
class DatabaseConfig:
    """Database configuration."""

    def __init__(self, database_url: str, echo: bool = False) -> None:
        """Initialize database configuration."""
        self.database_url = database_url
        self.echo = echo
        self._schema_ready = False
        self._auto_create_schema = "sqlite" in database_url
        self._memory_db = ":memory:" in database_url

        is_sqlite = "sqlite" in database_url
        connect_args: dict[str, Any] | None = None
        if is_sqlite:
            connect_args = {"check_same_thread": False}

        # Create async engine
        engine_kwargs: dict[str, Any] = {"echo": echo}
        if is_sqlite:
            engine_kwargs["poolclass"] = StaticPool
        if connect_args:
            engine_kwargs["connect_args"] = connect_args

        self.engine = create_async_engine(
            database_url,
            **engine_kwargs,
        )

        # Create session factory
        self.async_session_maker = async_sessionmaker(
            self.engine,
            class_=SchemaAwareSession,
            expire_on_commit=False,
            _db_config=self,
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
    if config._auto_create_schema and (config._memory_db or not config._schema_ready):
        import modules.workspace.db.tables  # noqa: F401
        await _create_schema(config)
    async with config.async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def _create_schema(config: DatabaseConfig) -> None:
    """Create schema using a sync engine to avoid async DDL stalls."""
    await asyncio.to_thread(Base.metadata.create_all, config.engine.sync_engine)
    config._schema_ready = True
