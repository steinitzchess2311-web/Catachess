"""
Discussion thread endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from workspace.api.deps import get_current_user_id
from workspace.api.schemas.discussion_thread import (
    ThreadCreate,
    ThreadResponse,
    ThreadUpdate,
)
from workspace.db.repos.discussion_thread_repo import DiscussionThreadRepository
from workspace.domain.models.discussion_thread import (
    CreateThreadCommand,
    UpdateThreadCommand,
)
from workspace.domain.services.discussion.thread_service import (
    ThreadNotFoundError,
    ThreadService,
)

router = APIRouter(prefix="/discussions", tags=["discussions"])


async def get_thread_service() -> ThreadService:
    raise NotImplementedError("DI not configured")


async def get_thread_repo() -> DiscussionThreadRepository:
    raise NotImplementedError("DI not configured")


@router.post("", response_model=ThreadResponse, status_code=status.HTTP_201_CREATED)
async def create_thread(
    data: ThreadCreate,
    user_id: str = Depends(get_current_user_id),
    service: ThreadService = Depends(get_thread_service),
) -> ThreadResponse:
    try:
        command = CreateThreadCommand(
            target_id=data.target_id,
            target_type=data.target_type,
            author_id=user_id,
            title=data.title,
            content=data.content,
            thread_type=data.thread_type,
        )
        thread = await service.create_thread(command)
        return ThreadResponse.model_validate(thread)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("", response_model=list[ThreadResponse])
async def list_threads(
    target_id: str,
    target_type: str,
    repo: DiscussionThreadRepository = Depends(get_thread_repo),
) -> list[ThreadResponse]:
    threads = await repo.list_by_target(target_id, target_type)
    return [ThreadResponse.model_validate(thread) for thread in threads]


@router.put("/{thread_id}", response_model=ThreadResponse)
async def update_thread(
    thread_id: str,
    data: ThreadUpdate,
    user_id: str = Depends(get_current_user_id),
    service: ThreadService = Depends(get_thread_service),
) -> ThreadResponse:
    try:
        command = UpdateThreadCommand(
            thread_id=thread_id,
            title=data.title,
            content=data.content,
            actor_id=user_id,
            version=data.version,
        )
        thread = await service.update_thread(command)
        return ThreadResponse.model_validate(thread)
    except ThreadNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.delete("/{thread_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_thread(
    thread_id: str,
    service: ThreadService = Depends(get_thread_service),
) -> None:
    try:
        await service.delete_thread(thread_id)
    except ThreadNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
