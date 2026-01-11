"""
Discussion thread state endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from workspace.api.deps import get_current_user_id
from workspace.api.schemas.discussion_thread import ThreadPin, ThreadResolve, ThreadResponse
from workspace.domain.models.discussion_thread import PinThreadCommand, ResolveThreadCommand
from workspace.domain.services.discussion.thread_state_service import (
    ThreadNotFoundError,
    ThreadStateService,
)

router = APIRouter(prefix="/discussions", tags=["discussions"])


async def get_thread_state_service() -> ThreadStateService:
    raise NotImplementedError("DI not configured")


@router.patch("/{thread_id}/resolve", response_model=ThreadResponse)
async def resolve_thread(
    thread_id: str,
    data: ThreadResolve,
    user_id: str = Depends(get_current_user_id),
    service: ThreadStateService = Depends(get_thread_state_service),
) -> ThreadResponse:
    try:
        command = ResolveThreadCommand(
            thread_id=thread_id,
            actor_id=user_id,
            resolved=data.resolved,
            version=data.version,
        )
        thread = await service.resolve_thread(command)
        return ThreadResponse.model_validate(thread)
    except ThreadNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.patch("/{thread_id}/pin", response_model=ThreadResponse)
async def pin_thread(
    thread_id: str,
    data: ThreadPin,
    user_id: str = Depends(get_current_user_id),
    service: ThreadStateService = Depends(get_thread_state_service),
) -> ThreadResponse:
    try:
        command = PinThreadCommand(
            thread_id=thread_id,
            actor_id=user_id,
            pinned=data.pinned,
            version=data.version,
        )
        thread = await service.pin_thread(command)
        return ThreadResponse.model_validate(thread)
    except ThreadNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
