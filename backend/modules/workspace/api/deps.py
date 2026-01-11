from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from workspace.db.repos.acl_repo import ACLRepository
from workspace.db.repos.discussion_reply_repo import DiscussionReplyRepository
from workspace.db.repos.discussion_thread_repo import DiscussionThreadRepository
from workspace.db.repos.event_repo import EventRepository
from workspace.db.repos.node_repo import NodeRepository
from workspace.db.repos.search_index_repo import SearchIndexRepository
from workspace.db.session import get_session
from workspace.domain.services.node_service import NodeService
from workspace.domain.services.share_service import ShareService
from workspace.events.bus import EventBus
from workspace.events.subscribers.search_indexer import register_search_indexer
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


async def get_node_repo(
    session: AsyncSession = Depends(get_session),
) -> NodeRepository:
    return NodeRepository(session)


async def get_acl_repo(
    session: AsyncSession = Depends(get_session),
) -> ACLRepository:
    return ACLRepository(session)


async def get_event_repo(
    session: AsyncSession = Depends(get_session),
) -> EventRepository:
    return EventRepository(session)


async def get_event_bus(
    session: AsyncSession = Depends(get_session),
) -> EventBus:
    bus = EventBus(session)
    register_search_indexer(
        bus,
        DiscussionThreadRepository(session),
        DiscussionReplyRepository(session),
        SearchIndexRepository(session),
    )
    return bus


async def get_node_service(
    session: AsyncSession = Depends(get_session),
    node_repo: NodeRepository = Depends(get_node_repo),
    acl_repo: ACLRepository = Depends(get_acl_repo),
    event_bus: EventBus = Depends(get_event_bus),
) -> NodeService:
    return NodeService(session, node_repo, acl_repo, event_bus)


async def get_share_service(
    session: AsyncSession = Depends(get_session),
    node_repo: NodeRepository = Depends(get_node_repo),
    acl_repo: ACLRepository = Depends(get_acl_repo),
    event_bus: EventBus = Depends(get_event_bus),
) -> ShareService:
    return ShareService(session, node_repo, acl_repo, event_bus)
