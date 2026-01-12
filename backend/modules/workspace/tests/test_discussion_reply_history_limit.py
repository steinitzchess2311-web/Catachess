"""
Discussion reply history limit API test.
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
async def test_reply_history_limit(app: FastAPI):
    
    await init_test_db()
    headers = {"Authorization": "Bearer user123"}
    config = get_db_config()
    async with config.async_session_maker() as session:
        await create_study_node(session, "study-2", "user123")
        await session.commit()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        thread_resp = await client.post(
            "/discussions",
            json={
                "target_id": "study-2",
                "target_type": "study",
                "title": "Limit",
                "content": "Root",
                "thread_type": "note",
            },
            headers=headers,
        )
        thread_id = thread_resp.json()["id"]
        reply_resp = await client.post(
            f"/discussions/{thread_id}/replies",
            json={"content": "v0"},
            headers=headers,
        )
        reply_id = reply_resp.json()["id"]
        version = reply_resp.json()["version"]
        for idx in range(12):
            edit_resp = await client.put(
                f"/replies/{reply_id}",
                json={"content": f"v{idx + 1}", "version": version},
                headers=headers,
            )
            version = edit_resp.json()["version"]
        history_resp = await client.get(
            f"/replies/{reply_id}/history",
            headers=headers,
        )

    data = history_resp.json()
    assert len(data) == 10
    assert data[0]["content"] == "v2"
