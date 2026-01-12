import asyncio
import os
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

import workspace.db.tables  # noqa: F401
from workspace.db.base import Base
from workspace.db.repos.acl_repo import ACLRepository
from workspace.db.repos.event_repo import EventRepository
from workspace.db.repos.node_repo import NodeRepository
from workspace.db.repos.variation_repo import VariationRepository
from workspace.db.session import get_db_config, init_db
from workspace.domain.services.node_service import NodeService
from workspace.domain.services.share_service import ShareService
from workspace.events.bus import EventBus
from workspace.events.subscribers.registry import register_all_subscribers

os.environ.setdefault("WORKSPACE_TEST_AUTH", "1")

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def engine():
    config = init_db("sqlite+aiosqlite:///:memory:", echo=False)
    async with config.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    config._schema_ready = True

    yield config.engine

    await config.engine.dispose()


@pytest_asyncio.fixture
async def session(engine) -> AsyncGenerator[AsyncSession, None]:
    config = get_db_config()
    async with config.async_session_maker() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def node_repo(session: AsyncSession) -> NodeRepository:
    return NodeRepository(session)


@pytest_asyncio.fixture
async def acl_repo(session: AsyncSession) -> ACLRepository:
    return ACLRepository(session)


@pytest_asyncio.fixture
async def event_repo(session: AsyncSession) -> EventRepository:
    return EventRepository(session)


@pytest_asyncio.fixture
async def event_bus(session: AsyncSession) -> EventBus:
    bus = EventBus(session)
    register_all_subscribers(bus, session)
    return bus


@pytest_asyncio.fixture
async def variation_repo(session: AsyncSession) -> VariationRepository:
    return VariationRepository(session)


@pytest_asyncio.fixture
async def node_service(
    session: AsyncSession,
    node_repo: NodeRepository,
    acl_repo: ACLRepository,
    event_bus: EventBus,
) -> NodeService:
    return NodeService(session, node_repo, acl_repo, event_bus)


@pytest_asyncio.fixture
async def share_service(
    session: AsyncSession,
    node_repo: NodeRepository,
    acl_repo: ACLRepository,
    event_bus: EventBus,
) -> ShareService:
    return ShareService(session, node_repo, acl_repo, event_bus)
