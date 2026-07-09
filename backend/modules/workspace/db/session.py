"""
Created at: 2026-07-09 01:16 EDT
Created by: Codex
Last Modified at: 2026-07-09 01:16 EDT
Last Modified by: Codex

Database session management.
"""

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
        if config and config._auto_create_schema and not config._schema_ready:
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
        else:
            # PostgreSQL connection pool optimization (use same config as sync engine)
            try:
                from core.config import settings
                engine_kwargs["pool_size"] = settings.DB_POOL_SIZE
                engine_kwargs["max_overflow"] = settings.DB_MAX_OVERFLOW
                engine_kwargs["pool_recycle"] = settings.DB_POOL_RECYCLE
                engine_kwargs["pool_timeout"] = settings.DB_POOL_TIMEOUT
            except Exception:
                # Fallback to hardcoded values if settings not available
                engine_kwargs["pool_size"] = 20
                engine_kwargs["max_overflow"] = 40
                engine_kwargs["pool_recycle"] = 3600
                engine_kwargs["pool_timeout"] = 30
            engine_kwargs["pool_pre_ping"] = True
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
    if config._auto_create_schema and not config._schema_ready:
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
    """Create schema using the async engine used by workspace tests."""
    async with config.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    config._schema_ready = True
