"""
Tests for PGN clip/export endpoints.
"""

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from workspace.api.endpoints.studies import get_pgn_clip_service
from workspace.api.router import api_router
from workspace.db.repos.event_repo import EventRepository
from workspace.db.repos.study_repo import StudyRepository
from workspace.db.repos.variation_repo import VariationRepository
from workspace.db.session import get_db_config, init_db
from workspace.db.tables.nodes import Node
from workspace.db.tables.studies import Chapter, Study
from workspace.domain.models.types import NodeType, Visibility
from workspace.domain.services.pgn_clip_service import PgnClipService
from workspace.events.bus import EventBus


PGN_SAMPLE = """
[Event "Test Game"]

1. e4 (1. d4 d5 2. c4) e5 (1...c5 2. Nf3) 2. Nf3 (2. Bc4) Nc6 3. Bb5 *
"""


class StubR2Client:
    def __init__(self, pgn_text: str) -> None:
        self.pgn_text = pgn_text

    def download_pgn(self, key: str) -> str:
        return self.pgn_text


@pytest.fixture
def app() -> FastAPI:
    app = FastAPI()
    app.include_router(api_router)
    return app


async def seed_chapter() -> None:
    config = get_db_config()
    async with config.async_session_maker() as session:
        node = Node(
            id="study-1",
            node_type=NodeType.STUDY,
            title="Test Study",
            description=None,
            owner_id="user-1",
            visibility=Visibility.PRIVATE,
            parent_id=None,
            path="/study-1/",
            depth=0,
            layout={},
            version=1,
        )
        study = Study(
            id="study-1",
            description=None,
            chapter_count=1,
            is_public=False,
            tags=None,
        )
        chapter = Chapter(
            id="chapter-1",
            study_id="study-1",
            title="Chapter 1",
            order=0,
            white=None,
            black=None,
            event=None,
            date=None,
            result=None,
            r2_key="r2://chapter-1",
            pgn_hash=None,
            pgn_size=None,
            r2_etag=None,
            last_synced_at=None,
        )
        session.add_all([node, study, chapter])
        await session.commit()


async def override_pgn_clip_service() -> PgnClipService:
    config = get_db_config()
    async with config.async_session_maker() as session:
        study_repo = StudyRepository(session)
        chap = await study_repo.get_chapter_by_id("chapter-1")
        print(f"DEBUG: Chapter found in override? {chap}")
        
        event_bus = EventBus(session)
        service = PgnClipService(
            study_repo=study_repo,
            variation_repo=VariationRepository(session),
            event_repo=EventRepository(session),
            event_bus=event_bus,
            r2_client=StubR2Client(PGN_SAMPLE),
        )
        yield service


@pytest.mark.asyncio
async def test_preview_clip_endpoint(app: FastAPI):
    init_db("sqlite+aiosqlite:///:memory:", echo=False)
    await seed_chapter()
    app.dependency_overrides[get_pgn_clip_service] = override_pgn_clip_service

    headers = {"Authorization": "Bearer user-1"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/studies/study-1/pgn/clip/preview",
            params={"chapter_id": "chapter-1", "move_path": "main.2"},
            headers=headers,
        )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["moves_before"] >= 1


@pytest.mark.asyncio
async def test_export_no_comment_endpoint(app: FastAPI):
    init_db("sqlite+aiosqlite:///:memory:", echo=False)
    await seed_chapter()
    app.dependency_overrides[get_pgn_clip_service] = override_pgn_clip_service

    headers = {"Authorization": "Bearer user-1"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/studies/study-1/pgn/export/no-comment",
            json={"chapter_id": "chapter-1", "for_clipboard": True},
            headers=headers,
        )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert "pgn_text" in response.json()


@pytest.mark.asyncio
async def test_export_raw_endpoint(app: FastAPI):
    init_db("sqlite+aiosqlite:///:memory:", echo=False)
    await seed_chapter()
    app.dependency_overrides[get_pgn_clip_service] = override_pgn_clip_service

    headers = {"Authorization": "Bearer user-1"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/studies/study-1/pgn/export/raw",
            json={"chapter_id": "chapter-1", "for_clipboard": True},
            headers=headers,
        )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert "pgn_text" in response.json()


@pytest.mark.asyncio
async def test_export_clean_endpoint(app: FastAPI):
    init_db("sqlite+aiosqlite:///:memory:", echo=False)
    await seed_chapter()
    app.dependency_overrides[get_pgn_clip_service] = override_pgn_clip_service

    headers = {"Authorization": "Bearer user-1"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/studies/study-1/pgn/export/clean",
            json={"chapter_id": "chapter-1", "for_clipboard": True},
            headers=headers,
        )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["export_mode"] == "clean"
