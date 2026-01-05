"""
Assignments Router - Teacher-only business endpoint

Purpose:
    Demonstrate that authentication and authorization work in practice.
    This is a minimal business endpoint to verify:
    - JWT authentication works (401 when not authenticated)
    - Teacher permissions work (403 when student tries to access)
    - Teacher can successfully access (200 with teacher_id)

Endpoints:
    POST /assignments/ - Create an assignment (teacher-only)
    GET /assignments/ - List all assignments (teacher-only)
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from models.user import User
from core.security.deps import get_teacher_user
from core.log.log_api import logger


router = APIRouter(prefix="/assignments", tags=["assignments"])


class AssignmentCreateRequest(BaseModel):
    title: str
    description: str | None = None


class AssignmentResponse(BaseModel):
    ok: bool
    teacher_id: str
    teacher_username: str
    assignment: dict


@router.post("/", response_model=AssignmentResponse)
def create_assignment(
    request: AssignmentCreateRequest,
    teacher: User = Depends(get_teacher_user),
):
    """
    Create a new assignment (teacher-only).

    This endpoint demonstrates that:
    - Authentication works (requires valid JWT token)
    - Authorization works (requires teacher role)
    - Teacher identity is available in the endpoint

    Args:
        request: Assignment creation data
        teacher: Authenticated teacher user (auto-injected)

    Returns:
        Success response with teacher info and assignment data

    Raises:
        401: Not authenticated (no token or invalid token)
        403: Not authorized (student trying to access teacher endpoint)
    """
    logger.info(f"Teacher {teacher.username} creating assignment: {request.title}")

    # In a real system, this would save to database
    # For now, just return success with the data
    assignment_data = {
        "title": request.title,
        "description": request.description,
        "created_by": str(teacher.id),
    }

    logger.info(f"Assignment created successfully by teacher {teacher.username}")

    return AssignmentResponse(
        ok=True,
        teacher_id=str(teacher.id),
        teacher_username=teacher.username,
        assignment=assignment_data,
    )


@router.get("/")
def list_assignments(
    teacher: User = Depends(get_teacher_user),
):
    """
    List all assignments (teacher-only).

    Another endpoint to verify authorization works.

    Args:
        teacher: Authenticated teacher user (auto-injected)

    Returns:
        List of assignments (empty for now)

    Raises:
        401: Not authenticated
        403: Not authorized (student)
    """
    logger.info(f"Teacher {teacher.username} listing assignments")

    # In a real system, this would query the database
    # For now, return empty list
    return {
        "ok": True,
        "teacher_id": str(teacher.id),
        "teacher_username": teacher.username,
        "assignments": [],
    }
