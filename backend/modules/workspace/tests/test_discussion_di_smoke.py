"""
Discussion API DI smoke test.
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
async def test_discussion_di_smoke(app: FastAPI):
    await init_test_db()
    config = get_db_config()
    async with config.async_session_maker() as session:
        await create_study_node(session, "study-7", "user-1")
        await session.commit()

    headers = {"Authorization": "Bearer user-1"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        thread_resp = await client.post(
            "/discussions",
            json={
                "target_id": "study-7",
                "target_type": "study",
                "title": "Smoke",
                "content": "Root",
                "thread_type": "note",
            },
            headers=headers,
        )
        assert thread_resp.status_code == 201
