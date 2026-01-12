from fastapi import Header, HTTPException, status

from workspace.api.deps_core import (
    get_acl_repo,
    get_audit_repo,
    get_discussion_service,
    get_event_bus,
    get_event_repo,
    get_node_repo,
    get_node_service,
    get_presence_service,
    get_rate_limiter,
    get_share_service,
)
from workspace.api.discussion_deps import (
    get_reaction_repo,
    get_reaction_service,
    get_reply_repo,
    get_reply_service,
    get_thread_repo,
    get_thread_service,
    get_thread_state_service,
)


async def get_current_user_id(
    authorization: str | None = Header(None)
) -> str:
    if authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    if authorization.startswith("Bearer "):
        user_id = authorization[7:]
        if user_id:
            return user_id
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication",
    )
