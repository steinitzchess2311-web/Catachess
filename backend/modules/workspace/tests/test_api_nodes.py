"""
API tests for node endpoints.
"""

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

import modules.workspace.api.endpoints.nodes as node_endpoints
from modules.workspace.api.router import api_router
from modules.workspace.db.repos.study_repo import StudyRepository
from modules.workspace.db.session import get_db_config
from modules.workspace.storage.r2_client import UploadResult
from modules.workspace.domain.models.types import NodeType


@pytest.fixture
def app() -> FastAPI:
    """Create FastAPI app for testing."""
    app = FastAPI()
    app.include_router(api_router)
    return app


@pytest.mark.asyncio
async def test_create_workspace_api(app: FastAPI, session):
    """Test creating workspace via API."""
    from modules.workspace.db.session import init_db

    # Initialize DB for API deps
    init_db("sqlite+aiosqlite:///:memory:", echo=False)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/nodes",
            json={
                "node_type": "workspace",
                "title": "My Workspace",
            },
            headers={"Authorization": "Bearer user123"},
        )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "My Workspace"
    assert data["node_type"] == "workspace"
    assert data["owner_id"] == "user123"


@pytest.mark.asyncio
async def test_create_study_node_api_creates_default_chapter(app: FastAPI, session, monkeypatch):
    """Creating a study through /nodes creates the initial Chapter 1."""

    class FakeR2Client:
        def upload_json(self, key: str, content: str, metadata: dict[str, str]):
            return UploadResult(
                key=key,
                etag="test-etag",
                size=len(content.encode("utf-8")),
                content_hash="test-hash",
            )

    monkeypatch.setattr(node_endpoints, "create_r2_client_from_env", lambda: FakeR2Client())

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/nodes",
            json={
                "node_type": "study",
                "title": "Opening Notes",
                "visibility": "private",
            },
            headers={"Authorization": "Bearer user123"},
        )

    assert response.status_code == 201
    study_id = response.json()["id"]

    config = get_db_config()
    async with config.async_session_maker() as verify_session:
        repo = StudyRepository(verify_session)
        chapters = await repo.get_chapters_for_study(study_id)
        study = await repo.get_study_by_id(study_id)

    assert study is not None
    assert study.chapter_count == 1
    assert len(chapters) == 1
    assert chapters[0].title == "Chapter 1"
    assert chapters[0].order == 0
    assert chapters[0].pgn_status == "ready"


@pytest.mark.asyncio
async def test_get_node_api(app: FastAPI, node_service):
    """Test getting node via API."""
    from modules.workspace.domain.models.node import CreateNodeCommand

    # Create node via service
    node = await node_service.create_node(
        CreateNodeCommand(
            node_type=NodeType.WORKSPACE,
            title="Test Workspace",
            owner_id="user123",
        ),
        actor_id="user123",
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            f"/nodes/{node.id}",
            headers={"Authorization": "Bearer user123"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == node.id
    assert data["title"] == "Test Workspace"


@pytest.mark.asyncio
async def test_update_node_api(app: FastAPI, node_service):
    """Test updating node via API."""
    from modules.workspace.domain.models.node import CreateNodeCommand

    node = await node_service.create_node(
        CreateNodeCommand(
            node_type=NodeType.WORKSPACE,
            title="Original Title",
            owner_id="user123",
        ),
        actor_id="user123",
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.put(
            f"/nodes/{node.id}",
            json={
                "title": "Updated Title",
                "version": 1,
            },
            headers={"Authorization": "Bearer user123"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["version"] == 2


@pytest.mark.asyncio
async def test_delete_node_api(app: FastAPI, node_service):
    """Test deleting node via API."""
    from modules.workspace.domain.models.node import CreateNodeCommand

    node = await node_service.create_node(
        CreateNodeCommand(
            node_type=NodeType.WORKSPACE,
            title="To Delete",
            owner_id="user123",
        ),
        actor_id="user123",
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.delete(
            f"/nodes/{node.id}?version=1",
            headers={"Authorization": "Bearer user123"},
        )

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_unauthorized_access(app: FastAPI):
    """Test that requests without auth are rejected."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/nodes/some-id")

    assert response.status_code == 401
