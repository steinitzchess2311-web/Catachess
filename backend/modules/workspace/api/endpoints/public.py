"""
Public endpoints — no authentication required.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from modules.workspace.db.session import get_session
from modules.workspace.db.repos.node_repo import NodeRepository

router = APIRouter(prefix="/public", tags=["public"])


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
