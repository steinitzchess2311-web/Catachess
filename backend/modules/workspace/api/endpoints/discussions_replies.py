"""
Discussion reply endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from workspace.api.deps import get_current_user_id
from workspace.api.schemas.discussion_reply import ReplyCreate, ReplyResponse, ReplyUpdate
from workspace.domain.models.discussion_reply import (
    AddReplyCommand,
    EditReplyCommand,
    DeleteReplyCommand,
)
from workspace.domain.services.discussion.reply_service import (
    ReplyNotFoundError,
    ReplyService,
)

router = APIRouter(tags=["discussions"])


async def get_reply_service() -> ReplyService:
    raise NotImplementedError("DI not configured")


@router.post(
    "/discussions/{thread_id}/replies",
    response_model=ReplyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_reply(
    thread_id: str,
    data: ReplyCreate,
    user_id: str = Depends(get_current_user_id),
    service: ReplyService = Depends(get_reply_service),
) -> ReplyResponse:
    try:
        command = AddReplyCommand(
            thread_id=thread_id,
            author_id=user_id,
            content=data.content,
            parent_reply_id=data.parent_reply_id,
            quote_reply_id=data.quote_reply_id,
        )
        reply = await service.add_reply(command)
        return ReplyResponse.model_validate(reply)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.put("/replies/{reply_id}", response_model=ReplyResponse)
async def edit_reply(
    reply_id: str,
    data: ReplyUpdate,
    user_id: str = Depends(get_current_user_id),
    service: ReplyService = Depends(get_reply_service),
) -> ReplyResponse:
    try:
        command = EditReplyCommand(
            reply_id=reply_id,
            content=data.content,
            actor_id=user_id,
            version=data.version,
        )
        reply = await service.edit_reply(command)
        return ReplyResponse.model_validate(reply)
    except ReplyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.delete("/replies/{reply_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reply(
    reply_id: str,
    user_id: str = Depends(get_current_user_id),
    service: ReplyService = Depends(get_reply_service),
) -> None:
    try:
        command = DeleteReplyCommand(reply_id=reply_id, actor_id=user_id)
        await service.delete_reply(command)
    except ReplyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
