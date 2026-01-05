"""
Auth Router - Authentication endpoints

Endpoints:
    POST /auth/register - Register new user
    POST /auth/login - Login and get access token

This is the HTTP boundary - it only glues components together:
    - Uses user_service for business logic
    - Uses JWT for token creation
    - Handles HTTP request/response format
    - Logs API operations
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel

from core.db.deps import get_db
from services.user_service import authenticate_user, create_user
from core.security.jwt import create_access_token
from core.log.log_api import logger
from core.errors import UserAlreadyExistsError, get_error_response, get_http_status_code

router = APIRouter(prefix="/auth", tags=["auth"])


# Request/Response Schemas
class RegisterRequest(BaseModel):
    identifier: str
    identifier_type: str = "email"
    password: str
    role: str = "student"
    username: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    username: str | None
    identifier: str
    role: str


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
):
    """
    Register a new user.

    Creates a new user account with hashed password.
    Does NOT automatically log in - client must call /login after registration.

    Args:
        request: Registration data (identifier, password, role, username)
        db: Database session (auto-injected)

    Returns:
        Created user information (without sensitive data)

    Raises:
        409: User with identifier already exists
        400: Invalid input data
    """
    logger.info(f"Registration attempt: identifier={request.identifier}, role={request.role}")

    try:
        user = create_user(
            db=db,
            identifier=request.identifier,
            identifier_type=request.identifier_type,
            password=request.password,
            role=request.role,
            username=request.username,
        )

        logger.info(f"User registered successfully: {user.username} (id={user.id})")

        return UserResponse(
            id=str(user.id),
            username=user.username,
            identifier=user.identifier,
            role=user.role,
        )

    except UserAlreadyExistsError as e:
        logger.warning(f"Registration failed: {e.message}")
        raise HTTPException(
            status_code=get_http_status_code(e),
            detail=get_error_response(e),
        )


@router.post("/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Login and receive access token.

    Validates credentials and returns JWT access token.
    Token should be included in subsequent requests as:
        Authorization: Bearer <token>

    Args:
        form_data: OAuth2 form (username=identifier, password)
        db: Database session (auto-injected)

    Returns:
        Access token and token type

    Raises:
        401: Invalid credentials or inactive user
    """
    # OAuth2PasswordRequestForm uses 'username' field, but we accept identifier
    identifier = form_data.username
    password = form_data.password

    logger.info(f"Login attempt: identifier={identifier}")

    # Authenticate user
    user = authenticate_user(db, identifier, password)

    if not user:
        logger.warning(f"Login failed: invalid credentials for {identifier}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    token = create_access_token(str(user.id))

    logger.info(f"Login successful: {user.username} (role={user.role})")

    return TokenResponse(
        access_token=token,
        token_type="bearer",
    )


class LoginRequest(BaseModel):
    identifier: str
    password: str


@router.post("/login/json", response_model=TokenResponse)
def login_json(
    request: LoginRequest,
    db: Session = Depends(get_db),
):
    """
    Login with JSON body (alternative to form data).

    Same as /login but accepts JSON instead of form data.
    Useful for non-browser clients.

    Args:
        request: Login credentials (identifier and password)
        db: Database session (auto-injected)

    Returns:
        Access token and token type

    Raises:
        401: Invalid credentials or inactive user
    """
    logger.info(f"JSON login attempt: identifier={request.identifier}")

    user = authenticate_user(db, request.identifier, request.password)

    if not user:
        logger.warning(f"JSON login failed: invalid credentials for {request.identifier}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    token = create_access_token(str(user.id))

    logger.info(f"JSON login successful: {user.username}")

    return TokenResponse(
        access_token=token,
        token_type="bearer",
    )
