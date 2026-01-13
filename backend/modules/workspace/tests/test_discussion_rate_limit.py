"""
Discussion rate limiting tests.
"""

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from workspace.api.deps import get_rate_limiter
from workspace.api.rate_limit import RateLimiter
from workspace.api.router import api_router
from workspace.db.session import get_db_config
from workspace.domain.models.types import Permission
from workspace.domain.policies.limits import DiscussionLimits
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
async def test_create_thread_rate_limited(app: FastAPI, monkeypatch):
    monkeypatch.setenv("DISABLE_RATE_LIMIT", "0")
    await init_test_db()
    await seed_acl(Permission.COMMENTER)
    monkeypatch.setattr(DiscussionLimits, "MAX_THREADS_PER_MINUTE", 1)
    limiter = RateLimiter()
    app.dependency_overrides[get_rate_limiter] = lambda: limiter

    headers = {"Authorization": "Bearer user-2"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        first = await client.post(
            "/discussions",
            json={
                "target_id": "study-1",
                "target_type": "study",
                "title": "First",
                "content": "Ok",
                "thread_type": "note",
            },
            headers=headers,
        )
        second = await client.post(
            "/discussions",
            json={
                "target_id": "study-1",
                "target_type": "study",
                "title": "Second",
                "content": "Rate limited",
                "thread_type": "note",
            },
            headers=headers,
        )

    app.dependency_overrides.clear()

    assert first.status_code == 201
    assert second.status_code == 429
