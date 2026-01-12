"""Audit logging for permission denials."""
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from workspace.api.router import api_router
from workspace.db.session import get_db_config
from workspace.db.base import Base
from workspace.db.tables.audit_log import AuditLog
from workspace.db.tables.discussion_threads import DiscussionThread, ThreadType
from workspace.domain.models.types import Permission
from workspace.tests.helpers.discussion_setup import init_test_db, create_study_node, grant_acl


@pytest.fixture
def app() -> FastAPI:
    app = FastAPI()
    app.include_router(api_router)
    return app


async def _seed(permission: Permission, with_thread: bool) -> None:
    config = get_db_config()
    import workspace.db.tables  # noqa: F401
    async with config.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    config._schema_ready = True
    async with config.async_session_maker() as session:
        await create_study_node(session, "study-1", "owner-1")
        await grant_acl(session, "study-1", "user-2", permission, "owner-1")
        if with_thread:
            session.add(
                DiscussionThread(
                    id="t1",
                    target_id="study-1",
                    target_type="study",
                    author_id="owner-1",
                    title="T",
                    content="C",
                    thread_type=ThreadType.NOTE,
                    pinned=False,
                    resolved=False,
                    version=1,
                )
            )
        await session.commit()


async def _count_denials() -> int:
    config = get_db_config()
    async with config.async_session_maker() as session:
        rows = (await session.execute(select(AuditLog))).scalars().all()
        return len([row for row in rows if row.action == "discussion.permission.denied"])


@pytest.mark.asyncio
async def test_create_thread_denial_logged(app: FastAPI):
    await init_test_db()
    await _seed(Permission.VIEWER, False)
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
    assert await _count_denials() == 1


@pytest.mark.asyncio
async def test_add_reply_denial_logged(app: FastAPI):
    await init_test_db()
    await _seed(Permission.VIEWER, True)
    headers = {"Authorization": "Bearer user-2"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/discussions/t1/replies",
            json={"content": "Denied"},
            headers=headers,
        )
    assert response.status_code == 403
    assert await _count_denials() == 1
