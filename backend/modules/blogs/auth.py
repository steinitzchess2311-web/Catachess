"""
Blog Authentication and Authorization

Permission levels:
- Public: Can view published articles
- Editor: Can create and edit articles
- Admin: Can delete articles and manage everything

Architecture:
- Blog data: Stored in BLOG_DATABASE_URL (独立数据库)
- User data: Stored in main DATABASE_URL (主应用数据库)
- JWT auth: Uses main app's JWT system
"""
import os
import uuid
from typing import Optional
from fastapi import Depends, HTTPException, Header, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

# Import User model and JWT from main app
import sys
from pathlib import Path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from models.user import User
from core.security.jwt import decode_token
from core.db.deps import get_db

# OAuth2 scheme for automatic token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def get_blog_db():
    """
    Get blog database session (BLOG_DATABASE_URL - 独立数据库)

    Blog articles, categories, and images are stored here.
    """
    db_url = os.getenv("BLOG_DATABASE_URL")
    if not db_url:
        raise HTTPException(status_code=500, detail="BLOG_DATABASE_URL not configured")

    engine = create_engine(db_url)
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token

    Uses main app's JWT system and queries User from main database.
    Blog endpoints can use this to verify user identity.

    Args:
        token: JWT token from Authorization header (auto-extracted)
        db: Main app database session (where users table is)

    Returns:
        Authenticated User object

    Raises:
        HTTPException: 401 if token invalid or user not found/inactive
    """
    # Decode JWT token to get user_id
    user_id = decode_token(token)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Load user from main database
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.get(User, user_uuid)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme_optional),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Return the current user if a valid JWT is present, otherwise return None.
    Used for public endpoints that show extra info when logged in (e.g. is_liked).
    """
    if not token:
        return None
    try:
        user_id = decode_token(token)
        if not user_id:
            return None
        user_uuid = uuid.UUID(user_id)
        user = db.get(User, user_uuid)
        return user if user and user.is_active else None
    except Exception:
        return None


def require_editor(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Require user to be editor or admin

    get_current_user already ensures user is authenticated (raises 401 if not).
    This function checks role permissions.
    """
    if current_user.role not in ["editor", "admin"]:
        raise HTTPException(
            status_code=403,
            detail="Editor or admin role required"
        )

    return current_user


def require_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Require user to be admin

    get_current_user already ensures user is authenticated (raises 401 if not).
    This function checks admin permission.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin role required"
        )

    return current_user
