"""
User Service - User business logic

Responsibilities:
    1. Check if user identifier exists
    2. Create new user (with hashed password)
    3. Authenticate user (verify password)

Does NOT handle:
    - JWT token creation (that's jwt.py)
    - HTTP requests/responses (that's routers)
    - Authorization checks (that's permissions.py)
"""
from sqlalchemy.orm import Session
from models.user import User
from core.security.password import hash_password, verify_password
from core.log.log_service import logger
from core.errors import UserAlreadyExistsError, InvalidCredentialsError, UserInactiveError


def get_user_by_identifier(db: Session, identifier: str) -> User | None:
    """
    Get user by identifier (email or phone).

    Args:
        db: Database session
        identifier: User identifier (email or phone)

    Returns:
        User object if found, None otherwise
    """
    logger.debug(f"Looking up user by identifier: {identifier}")
    user = db.query(User).filter(User.identifier == identifier).first()
    if user:
        logger.debug(f"User found: {user.username} (role={user.role})")
    else:
        logger.debug(f"User not found: {identifier}")
    return user


def create_user(
    db: Session,
    identifier: str,
    identifier_type: str,
    password: str,
    role: str = "student",
    username: str | None = None,
) -> User:
    """
    Create a new user with hashed password.

    Args:
        db: Database session
        identifier: User identifier (email or phone)
        identifier_type: Type of identifier ("email" or "phone")
        password: Plain text password (will be hashed)
        role: User role ("student" or "teacher")
        username: Optional username

    Returns:
        Created User object

    Raises:
        UserAlreadyExistsError: If user with identifier already exists
    """
    logger.info(f"Creating user: identifier={identifier}, type={identifier_type}, role={role}")

    # Check if user exists
    existing_user = get_user_by_identifier(db, identifier)
    if existing_user:
        logger.warning(f"User creation failed: identifier {identifier} already exists")
        raise UserAlreadyExistsError(identifier)

    # Hash password
    hashed_password = hash_password(password)

    # Create user
    user = User(
        identifier=identifier,
        identifier_type=identifier_type,
        hashed_password=hashed_password,
        role=role,
        username=username,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info(f"User created successfully: {user.username} (id={user.id}, role={user.role})")
    return user


def authenticate_user(db: Session, identifier: str, password: str) -> User | None:
    """
    Authenticate user by identifier and password.

    Args:
        db: Database session
        identifier: User identifier (email or phone)
        password: Plain text password

    Returns:
        User object if authentication successful, None otherwise
    """
    logger.info(f"Authentication attempt for: {identifier}")

    user = get_user_by_identifier(db, identifier)
    if not user:
        logger.warning(f"Authentication failed: user not found ({identifier})")
        return None

    if not verify_password(password, user.hashed_password):
        logger.warning(f"Authentication failed: invalid password for {identifier}")
        return None

    if not user.is_active:
        logger.warning(f"Authentication failed: user inactive ({identifier})")
        return None

    logger.info(f"Authentication successful: {user.username} (role={user.role})")
    return user
