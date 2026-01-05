"""
Permissions Module - Authorization Layer (Authority)

Purpose:
    Answers the question: "WHAT can this user do?"
    This is ONLY about PERMISSIONS/AUTHORIZATION, not IDENTITY.

Core Responsibilities:
    Permission checking functions that raise exceptions if user lacks authority.

What This Module DOES:
    ✓ require_teacher(user: User) -> None
        - Checks if user.role == "teacher"
        - Raises 403 Forbidden if not

    ✓ require_student(user: User) -> None
        - Checks if user.role == "student"
        - Raises 403 Forbidden if not

What This Module DOES NOT DO:
    ✗ Extract JWT token (that's current_user.py)
    ✗ Decode tokens (that's jwt.py)
    ✗ Query user from database by token (that's current_user.py)
    ✗ Return User objects (it only checks them)

Key Principle:
    Authorization = Prove you have permission to do something
    This assumes identity is already verified by current_user.py

Difference from Authentication:
    - Authentication (401): "I don't know who you are"
    - Authorization (403): "I know who you are, but you can't do this"
"""
from fastapi import HTTPException, status
from models.user import User
from core.log.log_auth import logger
from core.errors import TeacherAccessRequiredError, StudentAccessRequiredError


def require_teacher(user: User) -> None:
    """
    Verify that user has teacher role.

    Args:
        user: Authenticated user object

    Raises:
        HTTPException: 403 Forbidden if user is not a teacher

    Example:
        @router.post("/assignments")
        def create_assignment(user: User = Depends(get_current_user)):
            require_teacher(user)  # Raises 403 if not teacher
            # ... rest of logic
    """
    if user.role != "teacher":
        logger.warning(f"Teacher permission denied for user: {user.username} (role={user.role})")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teacher permission required",
        )

    logger.debug(f"Teacher permission granted: {user.username}")


def require_student(user: User) -> None:
    """
    Verify that user has student role.

    Args:
        user: Authenticated user object

    Raises:
        HTTPException: 403 Forbidden if user is not a student

    Example:
        @router.get("/assignments")
        def list_assignments(user: User = Depends(get_current_user)):
            require_student(user)  # Raises 403 if not student
            # ... rest of logic
    """
    if user.role != "student":
        logger.warning(f"Student permission denied for user: {user.username} (role={user.role})")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student permission required",
        )

    logger.debug(f"Student permission granted: {user.username}")
