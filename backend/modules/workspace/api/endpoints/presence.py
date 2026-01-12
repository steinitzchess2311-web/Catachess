"""
Presence endpoints for real-time collaboration.

Provides REST API for managing user presence in studies.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from workspace.api.schemas.presence import (
    HeartbeatRequest,
    PresenceSessionResponse,
    OnlineUsersResponse,
    OnlineUserResponse,
    CursorPositionResponse,
)
from workspace.domain.services.presence_service import (
    PresenceService,
    SessionNotFoundError,
)


router = APIRouter(prefix="/presence", tags=["presence"])


# Dependency injection function (to be implemented in api/deps.py)
async def get_presence_service() -> PresenceService:
    """Get presence service instance."""
    # This will be implemented properly in api/deps.py
    # For now, this is a placeholder
    raise NotImplementedError("Presence service dependency not configured")


# Dependency for getting current user (to be implemented in api/deps.py)
async def get_current_user_id() -> str:
    """Get current user ID from auth context."""
    # This will be implemented properly in api/deps.py
    # For now, this is a placeholder
    raise NotImplementedError("Auth dependency not configured")


@router.post("/heartbeat", response_model=PresenceSessionResponse)
async def send_heartbeat(
    data: HeartbeatRequest,
    user_id: str = Depends(get_current_user_id),
    presence_service: PresenceService = Depends(get_presence_service),
) -> PresenceSessionResponse:
    """
    Send a heartbeat to maintain presence in a study.

    Updates the user's active status and cursor position.
    Creates a new session if one doesn't exist.

    Args:
        data: Heartbeat request with study and cursor information
        user_id: Current user ID (from auth)
        presence_service: Presence service instance

    Returns:
        Updated presence session
    """
    session = await presence_service.heartbeat(
        user_id=user_id,
        study_id=data.study_id,
        chapter_id=data.chapter_id,
        move_path=data.move_path,
    )

    return PresenceSessionResponse.model_validate(session)


@router.get("/{study_id}", response_model=OnlineUsersResponse)
async def get_online_users(
    study_id: str,
    user_id: str = Depends(get_current_user_id),
    presence_service: PresenceService = Depends(get_presence_service),
) -> OnlineUsersResponse:
    """
    Get list of online users in a study.

    Args:
        study_id: Study ID
        user_id: Current user ID (from auth)
        presence_service: Presence service instance

    Returns:
        List of online users with their presence information

    Note:
        In a production system, this should check if the user
        has permission to view the study before returning presence info.
    """
    sessions = await presence_service.get_online_users(study_id)

    users = []
    for session in sessions:
        cursor = None
        if session.chapter_id:
            cursor = CursorPositionResponse(
                chapter_id=session.chapter_id,
                move_path=session.move_path
            )

        users.append(
            OnlineUserResponse(
                user_id=session.user_id,
                status=session.status,
                cursor_position=cursor,
                last_heartbeat=session.last_heartbeat,
            )
        )

    return OnlineUsersResponse(
        study_id=study_id,
        users=users,
        total=len(users),
    )


@router.delete("/{study_id}")
async def leave_study(
    study_id: str,
    user_id: str = Depends(get_current_user_id),
    presence_service: PresenceService = Depends(get_presence_service),
) -> dict:
    """
    Leave a study (remove presence session).

    Args:
        study_id: Study ID
        user_id: Current user ID (from auth)
        presence_service: Presence service instance

    Returns:
        Success message
    """
    try:
        await presence_service.leave_study(user_id=user_id, study_id=study_id)
        return {"status": "success", "message": "Left study successfully"}

    except SessionNotFoundError:
        # Not an error - user wasn't in the study
        return {"status": "success", "message": "No active session found"}
