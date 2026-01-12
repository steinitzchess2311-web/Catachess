"""
Discussion owner permission tests.
"""

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from workspace.api.router import api_router
from workspace.db.session import get_db_config
from workspace.tests.helpers.discussion_setup import init_test_db, create_study_node


@pytest.fixture
def app() -> FastAPI:
    app = FastAPI()
    app.include_router(api_router)
    return app


@pytest.mark.asyncio
async def test_owner_can_delete_thread(app: FastAPI):
    await init_test_db()
    config = get_db_config()
    async with config.async_session_maker() as session:
        await create_study_node(session, "study-11", "owner-1")
        await session.commit()
    headers = {"Authorization": "Bearer owner-1"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        thread_resp = await client.post(
            "/discussions",
            json={
                "target_id": "study-11",
                "target_type": "study",
                "title": "Thread",
                "content": "Root",
                "thread_type": "note",
            },
            headers=headers,
        )
        thread_id = thread_resp.json()["id"]
        response = await client.delete(
            f"/discussions/{thread_id}",
            headers=headers,
        )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_owner_can_delete_reply(app: FastAPI):
    await init_test_db()
    config = get_db_config()
    async with config.async_session_maker() as session:
        await create_study_node(session, "study-12", "owner-1")
        await session.commit()
    headers = {"Authorization": "Bearer owner-1"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        thread_resp = await client.post(
            "/discussions",
            json={
                "target_id": "study-12",
                "target_type": "study",
                "title": "Thread",
                "content": "Root",
                "thread_type": "note",
            },
            headers=headers,
        )
        thread_id = thread_resp.json()["id"]
        reply_resp = await client.post(
            f"/discussions/{thread_id}/replies",
            json={"content": "Reply"},
            headers=headers,
        )
        reply_id = reply_resp.json()["id"]
        response = await client.delete(
            f"/replies/{reply_id}",
            headers=headers,
        )
    assert response.status_code == 204
