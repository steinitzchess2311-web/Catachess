"""
Created at: 2026-07-09 01:10 EDT
Created by: Codex
Last Modified at: 2026-07-09 01:10 EDT
Last Modified by: Codex

Database engine configuration.
"""
from sqlalchemy import create_engine
from sqlalchemy.engine.url import make_url
from core.config import settings

engine_url = make_url(settings.DATABASE_URL)
engine_kwargs = {
    "pool_pre_ping": True,  # Check connection health before using.
    "echo_pool": False,    # Disable pool logging for performance.
}

if engine_url.get_backend_name() != "sqlite":
    engine_kwargs.update(
        {
            "pool_size": settings.DB_POOL_SIZE,
            "max_overflow": settings.DB_MAX_OVERFLOW,
            "pool_recycle": settings.DB_POOL_RECYCLE,
            "pool_timeout": settings.DB_POOL_TIMEOUT,
        }
    )

db_engine = create_engine(settings.DATABASE_URL, **engine_kwargs)
