"""
Discussion thread update permission tests.
"""

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from workspace.api.router import api_router
from workspace.db.session import get_db_config
from workspace.domain.models.types import Permission
from workspace.tests.helpers.discussion_setup import init_test_db, create_study_node, grant_acl


@pytest.fixture
def app() -> FastAPI:
    app = FastAPI()
    app.include_router(api_router)
    return app


async def seed_acl(permission: Permission) -> None:
    config = get_db_config()
    async with config.async_session_maker() as session:
        await create_study_node(session, "study-2", "owner-1")
        await grant_acl(session, "study-2", "user-2", permission, "owner-1")
        await session.commit()


@pytest.mark.asyncio
async def test_update_thread_requires_editor(app: FastAPI):
    await init_test_db()
    await seed_acl(Permission.VIEWER)
    owner_headers = {"Authorization": "Bearer owner-1"}
    editor_headers = {"Authorization": "Bearer user-2"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        create_resp = await client.post(
            "/discussions",
            json={
                "target_id": "study-2",
                "target_type": "study",
                "title": "Start",
                "content": "Root",
                "thread_type": "note",
            },
            headers=owner_headers,
        )
        thread_id = create_resp.json()["id"]
        response = await client.put(
            f"/discussions/{thread_id}",
            json={"title": "Edit", "content": "No", "version": 1},
            headers=editor_headers,
        )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_thread_allows_editor(app: FastAPI):
    await init_test_db()
    await seed_acl(Permission.EDITOR)
    owner_headers = {"Authorization": "Bearer owner-1"}
    editor_headers = {"Authorization": "Bearer user-2"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        create_resp = await client.post(
            "/discussions",
            json={
                "target_id": "study-2",
                "target_type": "study",
                "title": "Start",
                "content": "Root",
                "thread_type": "note",
            },
            headers=owner_headers,
        )
        thread_id = create_resp.json()["id"]
        response = await client.put(
            f"/discussions/{thread_id}",
            json={"title": "Edit", "content": "Yes", "version": 1},
            headers=editor_headers,
        )
    assert response.status_code == 200
