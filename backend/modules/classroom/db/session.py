"""
Classroom DB Session
====================
Uses CLASSROOM_DATABASE env var (Railway PostgreSQL, independent DB).
Synchronous SQLAlchemy — consistent with the catchat module pattern.
"""
import os

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all classroom ORM models."""
    pass


def _get_engine():
    url = os.getenv("CLASSROOM_DATABASE")
    if not url:
        raise HTTPException(status_code=500, detail="CLASSROOM_DATABASE not configured")
    return create_engine(url, pool_pre_ping=True)


def get_db():
    """FastAPI dependency: yields a classroom DB session."""
    db = Session(_get_engine())
    try:
        yield db
    finally:
        db.close()
