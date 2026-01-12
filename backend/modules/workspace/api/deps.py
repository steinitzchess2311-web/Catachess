import sys
import os
from pathlib import Path
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import uuid

# Add backend directory to path to import from core modules
backend_dir = Path(__file__).parent.parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from core.security.jwt import decode_token
from core.db.deps import get_db
from models.user import User

from workspace.api.deps_core import (
    get_acl_repo,
    get_audit_repo,
    get_discussion_service,
    get_event_bus,
    get_event_repo,
    get_node_repo,
    get_node_service,
    get_presence_service,
    get_rate_limiter,
    get_search_service,
    get_share_service,
)
from workspace.db.session import get_session
from workspace.db.repos.study_repo import StudyRepository
from workspace.db.repos.variation_repo import VariationRepository
from workspace.db.repos.event_repo import EventRepository
from workspace.domain.services.pgn_clip_service import PgnClipService
from workspace.events.bus import EventBus
from workspace.storage.r2_client import create_r2_client_from_env
from workspace.api.discussion_deps import (
    get_reaction_repo,
    get_reaction_service,
    get_reply_repo,
    get_reply_service,
    get_thread_repo,
    get_thread_service,
    get_thread_state_service,
)

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    x_user_id: str | None = Header(None, alias="X-User-ID"),
    db: Session = Depends(get_db),
) -> User:
    """
    Get current authenticated user from JWT token with proper validation.

    This replaces the insecure get_current_user_id that trusted raw Bearer tokens.
    Now properly decodes JWT, validates signature/expiry, and loads user from DB.
    """
    if os.getenv("WORKSPACE_TEST_AUTH") == "1":
        if x_user_id:
            return _build_test_user(x_user_id)
        if token:
            return _build_test_user(token)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Decode and validate JWT token
    user_id = decode_token(token)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Validate UUID format
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        if os.getenv("WORKSPACE_TEST_AUTH") == "1":
            return _build_test_user(user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Load user from database
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


async def get_current_user_id(
    user: User = Depends(get_current_user)
) -> str:
    """
    Get current user ID from authenticated user.

    This is a convenience wrapper that maintains backward compatibility
    with existing code that expects user_id as a string.
    """
    return str(user.id)


def _build_test_user(user_id: str) -> User:
    """Create a minimal user object for test auth bypass."""
    user = User()
    user.id = user_id
    user.username = None
    user.identifier = "test@example.com"
    user.identifier_type = "email"
    user.hashed_password = "test"
    user.role = "student"
    user.is_active = True
    return user


async def get_study_repository(
    session=Depends(get_session),
) -> StudyRepository:
    return StudyRepository(session)


async def get_variation_repository(
    session=Depends(get_session),
) -> VariationRepository:
    return VariationRepository(session)


async def get_pgn_clip_service(
    study_repo: StudyRepository = Depends(get_study_repository),
    variation_repo: VariationRepository = Depends(get_variation_repository),
    event_repo: EventRepository = Depends(get_event_repo),
    event_bus: EventBus = Depends(get_event_bus),
) -> PgnClipService:
    r2_client = create_r2_client_from_env()
    return PgnClipService(
        study_repo, variation_repo, event_repo, event_bus, r2_client
    )
