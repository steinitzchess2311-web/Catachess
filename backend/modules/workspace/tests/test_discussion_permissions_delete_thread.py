"""
Discussion thread delete permission tests.
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
        await create_study_node(session, "study-3", "owner-1")
        await grant_acl(session, "study-3", "user-2", permission, "owner-1")
        await session.commit()


@pytest.mark.asyncio
async def test_delete_thread_requires_admin(app: FastAPI):
    await init_test_db()
    await seed_acl(Permission.EDITOR)
    owner_headers = {"Authorization": "Bearer owner-1"}
    other_headers = {"Authorization": "Bearer user-2"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        create_resp = await client.post(
            "/discussions",
            json={
                "target_id": "study-3",
                "target_type": "study",
                "title": "Start",
                "content": "Root",
                "thread_type": "note",
            },
            headers=owner_headers,
        )
        thread_id = create_resp.json()["id"]
        response = await client.delete(
            f"/discussions/{thread_id}",
            headers=other_headers,
        )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_thread_allows_admin(app: FastAPI):
    await init_test_db()
    await seed_acl(Permission.ADMIN)
    owner_headers = {"Authorization": "Bearer owner-1"}
    admin_headers = {"Authorization": "Bearer user-2"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        create_resp = await client.post(
            "/discussions",
            json={
                "target_id": "study-3",
                "target_type": "study",
                "title": "Start",
                "content": "Root",
                "thread_type": "note",
            },
            headers=owner_headers,
        )
        thread_id = create_resp.json()["id"]
        response = await client.delete(
            f"/discussions/{thread_id}",
            headers=admin_headers,
        )
    assert response.status_code == 204
