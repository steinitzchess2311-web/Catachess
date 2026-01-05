"""
Dependencies Module - FastAPI Glue Layer

Purpose:
    Combines authentication + authorization into reusable FastAPI dependencies.
    This is the INTEGRATION layer between current_user and permissions.

Why This File Exists:
    Instead of writing this in every router:
        user = Depends(get_current_user)
        require_teacher(user)

    We create pre-combined dependencies:
        teacher = Depends(get_teacher_user)

Core Dependencies:
    1. get_teacher_user(user: User = Depends(get_current_user)) -> User
        - First authenticates user (get_current_user)
        - Then checks teacher permission (require_teacher)
        - Returns authenticated teacher User
        - Router doesn't need to know permission logic

    2. get_student_user(user: User = Depends(get_current_user)) -> User
        - Authenticates user
        - Checks student permission
        - Returns authenticated student User

Benefits:
    ✓ Routers stay clean and declarative
    ✓ Permission logic centralized
    ✓ Easy to add new role combinations
    ✓ Consistent error responses
    ✓ Type hints help IDEs and developers

Example Usage in Router:
    # Before (verbose):
    @router.post("/assignments")
    def create_assignment(
        assignment: AssignmentCreate,
        user: User = Depends(get_current_user)
    ):
        require_teacher(user)  # Easy to forget!
        return create_assignment_logic(assignment, user)

    # After (clean):
    @router.post("/assignments")
    def create_assignment(
        assignment: AssignmentCreate,
        teacher: User = Depends(get_teacher_user)
    ):
        return create_assignment_logic(assignment, teacher)

Key Principle:
    This is GLUE CODE - it connects pieces but doesn't implement logic.
    All real logic lives in current_user.py and permissions.py.
"""
from fastapi import Depends
from core.security.current_user import get_current_user
from core.security.permissions import require_teacher, require_student
from models.user import User


def get_teacher_user(
    user: User = Depends(get_current_user),
) -> User:
    """
    FastAPI dependency that returns an authenticated teacher.

    Combines:
    1. get_current_user() - authentication
    2. require_teacher() - authorization

    Args:
        user: Auto-injected authenticated user

    Returns:
        User object with teacher role

    Raises:
        HTTPException: 401 if not authenticated, 403 if not teacher

    Example:
        @router.post("/assignments")
        def create_assignment(teacher: User = Depends(get_teacher_user)):
            # teacher is guaranteed to be authenticated and have teacher role
            return {"teacher": teacher.username}
    """
    require_teacher(user)
    return user


def get_student_user(
    user: User = Depends(get_current_user),
) -> User:
    """
    FastAPI dependency that returns an authenticated student.

    Combines:
    1. get_current_user() - authentication
    2. require_student() - authorization

    Args:
        user: Auto-injected authenticated user

    Returns:
        User object with student role

    Raises:
        HTTPException: 401 if not authenticated, 403 if not student

    Example:
        @router.get("/my-assignments")
        def get_my_assignments(student: User = Depends(get_student_user)):
            # student is guaranteed to be authenticated and have student role
            return {"student": student.username}
    """
    require_student(user)
    return user
