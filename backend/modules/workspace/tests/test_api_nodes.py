"""
API tests for node endpoints.
"""

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from workspace.api.router import api_router
from workspace.domain.models.types import NodeType


@pytest.fixture
def app() -> FastAPI:
    """Create FastAPI app for testing."""
    app = FastAPI()
    app.include_router(api_router)
    return app


@pytest.mark.asyncio
async def test_create_workspace_api(app: FastAPI, session):
    """Test creating workspace via API."""
    from workspace.db.session import init_db

    # Initialize DB for API deps
    init_db("sqlite+aiosqlite:///:memory:", echo=False)

    async with AsyncClient(app=app, base_url="http://test") as client:
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
async def test_get_node_api(app: FastAPI, node_service):
    """Test getting node via API."""
    from workspace.domain.models.node import CreateNodeCommand

    # Create node via service
    node = await node_service.create_node(
        CreateNodeCommand(
            node_type=NodeType.WORKSPACE,
            title="Test Workspace",
            owner_id="user123",
        ),
        actor_id="user123",
    )

    async with AsyncClient(app=app, base_url="http://test") as client:
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
    from workspace.domain.models.node import CreateNodeCommand

    node = await node_service.create_node(
        CreateNodeCommand(
            node_type=NodeType.WORKSPACE,
            title="Original Title",
            owner_id="user123",
        ),
        actor_id="user123",
    )

    async with AsyncClient(app=app, base_url="http://test") as client:
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
    from workspace.domain.models.node import CreateNodeCommand

    node = await node_service.create_node(
        CreateNodeCommand(
            node_type=NodeType.WORKSPACE,
            title="To Delete",
            owner_id="user123",
        ),
        actor_id="user123",
    )

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.delete(
            f"/nodes/{node.id}?version=1",
            headers={"Authorization": "Bearer user123"},
        )

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_unauthorized_access(app: FastAPI):
    """Test that requests without auth are rejected."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/nodes/some-id")

    assert response.status_code == 401
