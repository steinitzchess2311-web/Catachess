"""
User search endpoints for workspace sharing.
"""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from modules.workspace.api.deps import get_current_user_id
from modules.workspace.api.deps_core import get_user_repo
from modules.workspace.db.repos.user_repo import UserRepository

router = APIRouter(prefix="/users", tags=["users"])


class UserSearchResult(BaseModel):
    id: str
    username: str


@router.get("/search", response_model=list[UserSearchResult])
async def search_users(
    q: str = Query(..., min_length=1, max_length=50),
    current_user_id: str = Depends(get_current_user_id),
    user_repo: UserRepository = Depends(get_user_repo),
) -> list[UserSearchResult]:
    """Search users by username prefix. Excludes the current user."""
    users = await user_repo.search_by_username(q)
    return [
        UserSearchResult(id=u.id, username=u.username)
        for u in users
        if u.id != current_user_id
    ]
