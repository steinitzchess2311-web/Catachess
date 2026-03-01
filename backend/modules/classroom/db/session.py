"""
Classroom DB Session
====================
Uses CLASSROOM_DATABASE env var (Railway PostgreSQL, independent DB).
Synchronous SQLAlchemy — consistent with the catchat module pattern.

Engine is created once at module load time (singleton) so that the
connection pool is reused across requests instead of being re-created
on every request (which wasted ~50 ms and exhausted the pool).
"""
import os

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all classroom ORM models."""
    pass


_url = os.getenv("CLASSROOM_DATABASE")
# Singleton engine — None when env var is not set (handled in get_db).
_engine = (
    create_engine(_url, pool_pre_ping=True, pool_size=5, max_overflow=10)
    if _url
    else None
)


def get_db():
    """FastAPI dependency: yields a classroom DB session."""
    if _engine is None:
        raise HTTPException(status_code=500, detail="CLASSROOM_DATABASE not configured")
    db = Session(_engine)
    try:
        yield db
    finally:
        db.close()
