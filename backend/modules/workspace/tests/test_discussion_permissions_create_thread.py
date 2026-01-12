"""
Discussion thread create permission tests.
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
        await create_study_node(session, "study-1", "owner-1")
        await grant_acl(session, "study-1", "user-2", permission, "owner-1")
        await session.commit()


@pytest.mark.asyncio
async def test_create_thread_requires_commenter(app: FastAPI):
    await init_test_db()
    await seed_acl(Permission.VIEWER)
    headers = {"Authorization": "Bearer user-2"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/discussions",
            json={
                "target_id": "study-1",
                "target_type": "study",
                "title": "Nope",
                "content": "Denied",
                "thread_type": "note",
            },
            headers=headers,
        )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_thread_allows_commenter(app: FastAPI):
    await init_test_db()
    await seed_acl(Permission.COMMENTER)
    headers = {"Authorization": "Bearer user-2"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/discussions",
            json={
                "target_id": "study-1",
                "target_type": "study",
                "title": "Ok",
                "content": "Allowed",
                "thread_type": "note",
            },
            headers=headers,
        )
    assert response.status_code == 201
