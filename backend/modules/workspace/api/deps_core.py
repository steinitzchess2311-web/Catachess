from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from modules.workspace.db.repos.acl_repo import ACLRepository
from modules.workspace.db.repos.user_repo import UserRepository
from modules.workspace.db.repos.audit_log_repo import AuditLogRepository
from modules.workspace.db.repos.discussion_reaction_repo import DiscussionReactionRepository
from modules.workspace.db.repos.discussion_reply_repo import DiscussionReplyRepository
from modules.workspace.db.repos.discussion_thread_repo import DiscussionThreadRepository
from modules.workspace.db.repos.event_repo import EventRepository
from modules.workspace.db.repos.node_repo import NodeRepository
from modules.workspace.db.repos.presence_repo import PresenceRepository
from modules.workspace.db.repos.search_index_repo import SearchIndexRepository
from modules.workspace.db.session import get_session
from modules.workspace.domain.services.discussion_service import DiscussionService
from modules.workspace.domain.services.node_service import NodeService
from modules.workspace.domain.services.presence_service import PresenceService
from modules.workspace.domain.services.search_service import SearchService
from modules.workspace.domain.services.share_service import ShareService
from modules.workspace.events.bus import EventBus
from modules.workspace.events.subscribers.registry import register_all_subscribers
from modules.workspace.api.rate_limit import RateLimiter

_rate_limiter = RateLimiter()

async def get_user_repo(
    session: AsyncSession = Depends(get_session),
) -> UserRepository:
    return UserRepository(session)


async def get_node_repo(
    session: AsyncSession = Depends(get_session),
) -> NodeRepository:
    return NodeRepository(session)


async def get_acl_repo(
    session: AsyncSession = Depends(get_session),
) -> ACLRepository:
    return ACLRepository(session)


async def get_audit_repo(
    session: AsyncSession = Depends(get_session),
) -> AuditLogRepository:
    return AuditLogRepository(session)


async def get_event_repo(
    session: AsyncSession = Depends(get_session),
) -> EventRepository:
    return EventRepository(session)


async def get_event_bus(
    session: AsyncSession = Depends(get_session),
) -> EventBus:
    bus = EventBus(session)
    register_all_subscribers(bus, session)
    return bus


async def get_rate_limiter() -> RateLimiter:
    return _rate_limiter


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


async def get_discussion_service(
    session: AsyncSession = Depends(get_session),
    event_bus: EventBus = Depends(get_event_bus),
) -> DiscussionService:
    thread_repo = DiscussionThreadRepository(session)
    reply_repo = DiscussionReplyRepository(session)
    reaction_repo = DiscussionReactionRepository(session)
    return DiscussionService(session, thread_repo, reply_repo, reaction_repo, event_bus)


async def get_presence_service(
    session: AsyncSession = Depends(get_session),
    event_bus: EventBus = Depends(get_event_bus),
) -> PresenceService:
    presence_repo = PresenceRepository(session)
    return PresenceService(session, presence_repo, event_bus)


async def get_search_service(
    session: AsyncSession = Depends(get_session),
    node_repo: NodeRepository = Depends(get_node_repo),
    acl_repo: ACLRepository = Depends(get_acl_repo),
) -> SearchService:
    search_repo = SearchIndexRepository(session)
    return SearchService(search_repo, node_repo, acl_repo)
