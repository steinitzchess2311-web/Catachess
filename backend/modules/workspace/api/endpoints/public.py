"""
Public endpoints — no authentication required.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from modules.workspace.api.deps import get_current_user_id
from modules.workspace.api.schemas.node import NodeListResponse, NodeResponse
from modules.workspace.db.session import get_session
from modules.workspace.db.repos.node_repo import NodeRepository

router = APIRouter(prefix="/public", tags=["public"])

# Browse router — handles /public-nodes and /shared-nodes at the workspace root
browse_router = APIRouter(tags=["public"])


@router.get("/studies")
async def list_public_studies(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    """
    List all public studies, newest first.

    No authentication required.
    """
    repo = NodeRepository(session)
    nodes = await repo.get_public_studies(limit=limit, offset=offset)
    return {
        "items": [
            {
                "id": n.id,
                "title": n.title,
                "owner_id": n.owner_id,
                "created_at": n.created_at.isoformat() if n.created_at else None,
                "updated_at": n.updated_at.isoformat() if n.updated_at else None,
            }
            for n in nodes
        ],
        "limit": limit,
        "offset": offset,
    }


@browse_router.get("/public-nodes", response_model=NodeListResponse)
async def list_public_nodes(
    parent_id: str | None = Query(None),
    session: AsyncSession = Depends(get_session),
) -> NodeListResponse:
    """
    Browse the public node tree.

    - parent_id omitted or "root": top-level public folders/studies
    - parent_id UUID: children of that public folder

    No authentication required.
    """
    repo = NodeRepository(session)
    nodes = await repo.get_public_nodes(parent_id=parent_id)
    return NodeListResponse(
        nodes=[NodeResponse.model_validate(n) for n in nodes],
        total=len(nodes),
    )


@browse_router.get("/shared-nodes", response_model=NodeListResponse)
async def list_shared_nodes(
    parent_id: str | None = Query(None),
    user_id: str = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> NodeListResponse:
    """
    Browse nodes shared with the current user.

    - parent_id omitted or "root": all nodes directly shared with user
    - parent_id UUID: children inside a shared folder

    Authentication required.
    """
    repo = NodeRepository(session)
    nodes = await repo.get_shared_nodes(user_id=user_id, parent_id=parent_id)
    return NodeListResponse(
        nodes=[NodeResponse.model_validate(n) for n in nodes],
        total=len(nodes),
    )
