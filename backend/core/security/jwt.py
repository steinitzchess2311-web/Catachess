"""
JWT Module - Token Encoding & Decoding

Purpose:
    Handles JWT (JSON Web Token) creation and validation for stateless authentication.

Responsibilities:
    1. create_access_token(user_id: str) -> str
       - Encodes user data (user_id) into JWT
       - Adds expiration time
       - Signs with SECRET_KEY
       - Returns token string

    2. decode_token(token: str) -> str | None
       - Decodes JWT token
       - Verifies signature and expiration
       - Returns user_id (from 'sub' field)
       - Returns None if invalid/expired

Token Payload Contains:
    - sub: subject (user_id)
    - exp: expiration timestamp
    - iat: issued at timestamp (automatic)

Security Considerations:
    - Use strong SECRET_KEY (from environment)
    - Set appropriate expiration times (60 minutes default)
    - Use HS256 algorithm
    - Never put sensitive data in payload (it's base64, not encrypted)

Example Flow:
    Login success -> create_access_token(user_id) -> return to client
    Request -> extract token -> decode_token() -> get user_id
"""
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError

from core.config import settings
from core.log.log_auth import logger


def create_access_token(user_id: str) -> str:
    """
    Create a JWT access token for a user.

    Args:
        user_id: User ID to encode in token (as string)

    Returns:
        JWT token string

    Example:
        token = create_access_token("123e4567-e89b-12d3-a456-426614174000")
    """
    # Use timezone-aware datetime
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": user_id,
        "exp": expire,
    }

    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    logger.info(f"Access token created for user_id={user_id}, expires in {settings.ACCESS_TOKEN_EXPIRE_MINUTES}m")

    return token


def decode_token(token: str) -> str | None:
    """
    Decode and verify a JWT token.

    Args:
        token: JWT token string

    Returns:
        User ID (from 'sub' field) if valid, None otherwise

    Example:
        user_id = decode_token("eyJ0eXAiOiJKV1QiLCJhbGc...")
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id = payload.get("sub")

        if not user_id:
            logger.warning("Token decoded but 'sub' field is missing")
            return None

        logger.debug(f"Token decoded successfully: user_id={user_id}")
        return user_id

    except JWTError as e:
        logger.warning(f"Token decode failed: {e}")
        return None
