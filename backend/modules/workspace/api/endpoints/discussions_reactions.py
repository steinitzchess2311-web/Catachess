"""
Discussion reaction endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from workspace.api.deps import get_current_user_id
from workspace.api.schemas.discussion_reaction import (
    ReactionCreate,
    ReactionResponse,
)
from workspace.domain.models.discussion_reaction import (
    AddReactionCommand,
    RemoveReactionCommand,
)
from workspace.domain.services.discussion.reaction_service import (
    ReactionNotFoundError,
    ReactionService,
)

router = APIRouter(prefix="/reactions", tags=["discussions"])


async def get_reaction_service() -> ReactionService:
    raise NotImplementedError("DI not configured")


@router.post("", response_model=ReactionResponse, status_code=status.HTTP_201_CREATED)
async def add_reaction(
    data: ReactionCreate,
    user_id: str = Depends(get_current_user_id),
    service: ReactionService = Depends(get_reaction_service),
) -> ReactionResponse:
    try:
        command = AddReactionCommand(
            target_id=data.target_id,
            target_type=data.target_type,
            user_id=user_id,
            emoji=data.emoji,
        )
        reaction = await service.add_reaction(command)
        return ReactionResponse.model_validate(reaction)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.delete("/{reaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_reaction(
    reaction_id: str,
    user_id: str = Depends(get_current_user_id),
    service: ReactionService = Depends(get_reaction_service),
) -> None:
    try:
        command = RemoveReactionCommand(reaction_id=reaction_id, user_id=user_id)
        await service.remove_reaction(command)
    except ReactionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
