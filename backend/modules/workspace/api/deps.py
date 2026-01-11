"""
Dependency injection helpers for FastAPI.
"""

from typing import AsyncGenerator

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from workspace.db.repos.acl_repo import ACLRepository
from workspace.db.repos.event_repo import EventRepository
from workspace.db.repos.node_repo import NodeRepository
from workspace.db.session import get_session
from workspace.domain.services.node_service import NodeService
from workspace.domain.services.share_service import ShareService
from workspace.events.bus import EventBus


# Authentication dependency (placeholder)
async def get_current_user_id(
    authorization: str | None = Header(None)
) -> str:
    """
    Get current authenticated user ID.

    This is a placeholder. In production, this would:
    - Verify JWT token
    - Check session
    - Return authenticated user ID

    For now, we'll extract user_id from a simple header.
    """
    if authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    # Simple format: "Bearer user_id"
    # In production: validate JWT and extract user_id
    if authorization.startswith("Bearer "):
        user_id = authorization[7:]
        if user_id:
            return user_id

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication",
    )


# Repository dependencies
async def get_node_repo(
    session: AsyncSession = Depends(get_session),
) -> NodeRepository:
    """Get node repository."""
    return NodeRepository(session)


async def get_acl_repo(
    session: AsyncSession = Depends(get_session),
) -> ACLRepository:
    """Get ACL repository."""
    return ACLRepository(session)


async def get_event_repo(
    session: AsyncSession = Depends(get_session),
) -> EventRepository:
    """Get event repository."""
    return EventRepository(session)


async def get_event_bus(
    session: AsyncSession = Depends(get_session),
) -> EventBus:
    """Get event bus."""
    return EventBus(session)


# Service dependencies
async def get_node_service(
    session: AsyncSession = Depends(get_session),
    node_repo: NodeRepository = Depends(get_node_repo),
    acl_repo: ACLRepository = Depends(get_acl_repo),
    event_bus: EventBus = Depends(get_event_bus),
) -> NodeService:
    """Get node service."""
    return NodeService(session, node_repo, acl_repo, event_bus)


async def get_share_service(
    session: AsyncSession = Depends(get_session),
    node_repo: NodeRepository = Depends(get_node_repo),
    acl_repo: ACLRepository = Depends(get_acl_repo),
    event_bus: EventBus = Depends(get_event_bus),
) -> ShareService:
    """Get share service."""
    return ShareService(session, node_repo, acl_repo, event_bus)
