"""
catchat DB Session
==================
Uses CATCHAT_DATABASE env var (private Railway PostgreSQL URL).
Independent from the main app database.
"""
import os

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all catchat ORM models."""
    pass


def _get_engine():
    url = os.getenv("CATCHAT_DATABASE")
    if not url:
        raise HTTPException(status_code=500, detail="CATCHAT_DATABASE not configured")
    return create_engine(url, pool_pre_ping=True)


def get_db():
    """FastAPI dependency: yields a catchat DB session."""
    db = Session(_get_engine())
    try:
        yield db
    finally:
        db.close()
