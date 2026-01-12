"""
Discussion reply edit history API tests.
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
async def test_reply_history_endpoint(app: FastAPI):
    
    await init_test_db()
    headers = {"Authorization": "Bearer user123"}
    config = get_db_config()
    async with config.async_session_maker() as session:
        await create_study_node(session, "study-1", "user123")
        await session.commit()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        thread_resp = await client.post(
            "/discussions",
            json={
                "target_id": "study-1",
                "target_type": "study",
                "title": "History",
                "content": "Root",
                "thread_type": "note",
            },
            headers=headers,
        )
        thread_id = thread_resp.json()["id"]
        reply_resp = await client.post(
            f"/discussions/{thread_id}/replies",
            json={"content": "First"},
            headers=headers,
        )
        reply_id = reply_resp.json()["id"]
        version = reply_resp.json()["version"]
        edit_resp = await client.put(
            f"/replies/{reply_id}",
            json={"content": "Second", "version": version},
            headers=headers,
        )
        version = edit_resp.json()["version"]
        edit_resp = await client.put(
            f"/replies/{reply_id}",
            json={"content": "Third", "version": version},
            headers=headers,
        )
        version = edit_resp.json()["version"]
        await client.put(
            f"/replies/{reply_id}",
            json={"content": "Fourth", "version": version},
            headers=headers,
        )
        history_resp = await client.get(
            f"/replies/{reply_id}/history",
            headers=headers,
        )

    data = history_resp.json()
    assert len(data) == 3
    assert data[0]["content"] == "First"
    assert data[0]["edited_by"] == "user123"
    assert data[1]["content"] == "Second"
