"""
Auth Router - Authentication endpoints

Endpoints:
    POST /auth/register - Register new user
    POST /auth/login - Login and get access token
    POST /auth/verify-signup - Verify signup with code
    POST /auth/resend-verification - Resend verification code

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
import uuid

from core.db.deps import get_db
from services.user_service import authenticate_user, create_user, get_user_by_identifier
from services.signup_verification_service import SignupVerificationService
from services.resend_email_service import ResendEmailService
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
    verification_sent: bool = False


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
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

        # Send verification code email (only for email users)
        verification_sent = False
        if request.identifier_type == "email":
            try:
                # Create verification code
                _, plain_code = SignupVerificationService.create_verification_code(
                    db=db,
                    user_id=user.id,
                    purpose="signup",
                )

                # Send email
                verification_sent = await ResendEmailService.send_verification_code(
                    to_email=user.identifier,
                    code=plain_code,
                    username=user.username,
                )

                if verification_sent:
                    logger.info(f"Verification email sent: {user.username} (id={user.id})")
                else:
                    logger.warning(f"Failed to send verification email: {user.username} (id={user.id})")

            except Exception as e:
                logger.error(f"Error sending verification email: {str(e)}", exc_info=True)
                # Don't fail registration if email fails
                verification_sent = False

        return UserResponse(
            id=str(user.id),
            username=user.username,
            identifier=user.identifier,
            role=user.role,
            verification_sent=verification_sent,
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


class VerifySignupRequest(BaseModel):
    identifier: str
    code: str


class VerifySignupResponse(BaseModel):
    success: bool
    message: str


@router.post("/verify-signup", response_model=VerifySignupResponse)
async def verify_signup(
    request: VerifySignupRequest,
    db: Session = Depends(get_db),
):
    """
    Verify signup with verification code.

    Validates the verification code sent to user's email/phone.
    Upon successful verification, the user account is marked as verified.

    Args:
        request: Verification data (identifier and code)
        db: Database session (auto-injected)

    Returns:
        Success status and message

    Raises:
        400: Invalid or expired verification code
        404: User not found
    """
    logger.info(f"Verification attempt: identifier={request.identifier}")

    # Get user by identifier
    user = get_user_by_identifier(db, request.identifier)
    if not user:
        logger.warning(f"Verification failed: user not found for {request.identifier}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Validate and consume code
    success, error_message = SignupVerificationService.validate_and_consume_code(
        db=db,
        user_id=user.id,
        plain_code=request.code,
        purpose="signup",
    )

    if not success:
        logger.warning(f"Verification failed: {error_message} for {request.identifier}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message,
        )

    # Mark user as verified (placeholder for future is_verified field)
    SignupVerificationService.mark_user_verified(db, user.id)

    logger.info(f"Verification successful: {user.username} (id={user.id})")

    return VerifySignupResponse(
        success=True,
        message="Account verified successfully",
    )


class ResendVerificationRequest(BaseModel):
    identifier: str


class ResendVerificationResponse(BaseModel):
    success: bool
    message: str


@router.post("/resend-verification", response_model=ResendVerificationResponse)
async def resend_verification(
    request: ResendVerificationRequest,
    db: Session = Depends(get_db),
):
    """
    Resend verification code.

    Generates a new verification code and sends it to the user's email.
    This invalidates any previous active codes for the user.

    Args:
        request: User identifier (email or phone)
        db: Database session (auto-injected)

    Returns:
        Success status and message

    Raises:
        404: User not found
        400: Failed to send email
    """
    logger.info(f"Resend verification attempt: identifier={request.identifier}")

    # Get user by identifier
    user = get_user_by_identifier(db, request.identifier)
    if not user:
        # Don't reveal if user exists (prevent enumeration)
        logger.warning(f"Resend verification: user not found for {request.identifier}")
        return ResendVerificationResponse(
            success=True,
            message="If the email exists, a verification code has been sent",
        )

    # Create new verification code
    _, plain_code = SignupVerificationService.create_verification_code(
        db=db,
        user_id=user.id,
        purpose="signup",
    )

    # Send email
    email_sent = await ResendEmailService.send_verification_code(
        to_email=user.identifier if user.identifier_type == "email" else None,
        code=plain_code,
        username=user.username,
    )

    if not email_sent:
        logger.error(f"Failed to send verification email for {request.identifier}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email",
        )

    logger.info(f"Verification code resent: {user.username} (id={user.id})")

    return ResendVerificationResponse(
        success=True,
        message="Verification code sent successfully",
    )
