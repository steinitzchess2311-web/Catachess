"""Database session helpers for Opening Trainer."""
from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from core.config import settings

_engine = None
_session_maker = None


def _resolve_db_url() -> str:
    db_url = os.getenv("OPENING_TRAINER_URL") or settings.DATABASE_URL
    if not db_url:
        raise RuntimeError("OPENING_TRAINER_URL (or DATABASE_URL fallback) is not configured")
    return db_url


def _get_session_maker() -> sessionmaker:
    global _engine, _session_maker
    if _session_maker is None:
        db_url = _resolve_db_url()
        _engine = create_engine(
            db_url,
            pool_pre_ping=True,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_recycle=settings.DB_POOL_RECYCLE,
            pool_timeout=settings.DB_POOL_TIMEOUT,
            echo_pool=False,
        )
        _session_maker = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=_engine,
        )
    return _session_maker


def get_opening_trainer_db():
    session_factory = _get_session_maker()
    db: Session = session_factory()
    try:
        yield db
    finally:
        db.close()

