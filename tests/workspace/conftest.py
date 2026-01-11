"""
Pytest fixtures for workspace tests.
"""

import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from workspace.db.base import Base
from workspace.db.repos.acl_repo import ACLRepository
from workspace.db.repos.event_repo import EventRepository
from workspace.db.repos.node_repo import NodeRepository
from workspace.db.repos.study_repo import StudyRepository
# Import all tables so they're registered with Base.metadata
from workspace.db.tables import acl, events, nodes, studies
from workspace.domain.services.chapter_import_service import ChapterImportService
from workspace.domain.services.node_service import NodeService
from workspace.domain.services.share_service import ShareService
from workspace.events.bus import EventBus
from workspace.storage.r2_client import R2Client, R2Config, UploadResult


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def engine():
    """Create test database engine."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def session(engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def node_repo(session: AsyncSession) -> NodeRepository:
    """Create node repository."""
    return NodeRepository(session)


@pytest_asyncio.fixture
async def acl_repo(session: AsyncSession) -> ACLRepository:
    """Create ACL repository."""
    return ACLRepository(session)


@pytest_asyncio.fixture
async def event_repo(session: AsyncSession) -> EventRepository:
    """Create event repository."""
    return EventRepository(session)


@pytest_asyncio.fixture
async def event_bus(session: AsyncSession) -> EventBus:
    """Create event bus."""
    return EventBus(session)


@pytest_asyncio.fixture
async def node_service(
    session: AsyncSession,
    node_repo: NodeRepository,
    acl_repo: ACLRepository,
    event_bus: EventBus,
) -> NodeService:
    """Create node service."""
    return NodeService(session, node_repo, acl_repo, event_bus)


@pytest_asyncio.fixture
async def share_service(
    session: AsyncSession,
    node_repo: NodeRepository,
    acl_repo: ACLRepository,
    event_bus: EventBus,
) -> ShareService:
    """Create share service."""
    return ShareService(session, node_repo, acl_repo, event_bus)


@pytest_asyncio.fixture
async def study_repo(session: AsyncSession) -> StudyRepository:
    """Create study repository."""
    return StudyRepository(session)


@pytest_asyncio.fixture
async def mock_r2_client() -> R2Client:
    """Create mock R2 client for testing."""

    class MockR2Client:
        """Mock R2 client that stores data in memory."""

        def __init__(self):
            self.storage = {}
            self.upload_count = 0

        def upload_pgn(self, key: str, content: str | bytes, **kwargs) -> UploadResult:
            """Mock upload - stores in memory."""
            if isinstance(content, str):
                content = content.encode("utf-8")

            self.storage[key] = content
            self.upload_count += 1

            # Calculate hash
            import hashlib
            content_hash = hashlib.sha256(content).hexdigest()

            return UploadResult(
                key=key,
                etag=f"mock-etag-{self.upload_count}",
                size=len(content),
                content_hash=content_hash,
            )

        def download_pgn(self, key: str) -> str:
            """Mock download - retrieves from memory."""
            if key not in self.storage:
                raise Exception(f"Key not found: {key}")
            return self.storage[key].decode("utf-8")

        def delete_object(self, key: str) -> None:
            """Mock delete."""
            if key in self.storage:
                del self.storage[key]

        def object_exists(self, key: str) -> bool:
            """Mock exists check."""
            return key in self.storage

    return MockR2Client()


@pytest_asyncio.fixture
async def chapter_import_service(
    node_service: NodeService,
    node_repo: NodeRepository,
    study_repo: StudyRepository,
    mock_r2_client: R2Client,
    event_bus: EventBus,
) -> ChapterImportService:
    """Create chapter import service."""
    return ChapterImportService(
        node_service=node_service,
        node_repo=node_repo,
        study_repo=study_repo,
        r2_client=mock_r2_client,
        event_bus=event_bus,
    )
