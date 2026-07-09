"""
Created at: 2026-07-09 01:20 EDT
Created by: Codex
Last Modified at: 2026-07-09 01:20 EDT
Last Modified by: Codex

Study permission collaboration tests covering read-only shared viewers,
editable shared editors, and chapter tree revision metadata.
"""

import json
from datetime import datetime, timezone

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

import patch.backend.study.api as patch_study_api
from modules.workspace.api.router import api_router
from modules.workspace.db.tables.acl import ACL
from modules.workspace.db.tables.studies import Chapter, Study
from modules.workspace.domain.models.node import CreateNodeCommand
from modules.workspace.domain.models.types import NodeType, Permission, Visibility
from modules.workspace.storage.r2_client import UploadResult


class FakeR2Client:
    """In-memory R2 substitute for tree save tests."""

    def __init__(self) -> None:
        self.objects: dict[str, str] = {}
        self.metadata: dict[str, dict[str, str]] = {}

    def exists(self, key: str) -> bool:
        return key in self.objects

    def download_json(self, key: str) -> str:
        return self.objects[key]

    def get_metadata(self, key: str) -> dict[str, str]:
        from botocore.exceptions import ClientError

        if key not in self.objects:
            raise ClientError(
                {"Error": {"Code": "NoSuchKey", "Message": "Missing"}},
                "HeadObject",
            )
        return self.metadata.get(key, {})

    def upload_json(self, key: str, content: str, metadata: dict[str, str] | None = None) -> UploadResult:
        self.objects[key] = content
        content_hash = "hash-" + str(len(content))
        self.metadata[key] = {"content-hash": content_hash}
        if metadata:
            self.metadata[key].update({k: v for k, v in metadata.items() if v is not None})
        return UploadResult(
            key=key,
            etag="etag-" + str(len(self.objects)),
            size=len(content.encode("utf-8")),
            content_hash=content_hash,
        )


@pytest.fixture
def app() -> FastAPI:
    """Create FastAPI app for testing."""
    app = FastAPI()
    app.include_router(api_router)
    return app


async def _seed_shared_study(session, node_service, acl_repo, permission: Permission) -> tuple[str, str, FakeR2Client]:
    study_node = await node_service.create_node(
        CreateNodeCommand(
            node_type=NodeType.STUDY,
            title="Shared Study",
            owner_id="owner-1",
            visibility=Visibility.SHARED,
        ),
        actor_id="owner-1",
    )
    study = Study(id=study_node.id, description=None, chapter_count=1, is_public=False, tags=None)
    session.add(study)

    tree = {
        "version": "v1",
        "rootId": "root",
        "nodes": {
            "root": {
                "id": "root",
                "parentId": None,
                "san": "",
                "children": [],
                "comment": None,
                "nags": [],
            },
        },
        "meta": {"result": "*"},
    }
    fake_r2 = FakeR2Client()
    chapter_id = "chapter-1"
    r2_key = f"chapters/{chapter_id}.tree.json"
    fake_r2.upload_json(r2_key, json.dumps(tree), metadata={"chapter_id": chapter_id})
    chapter = Chapter(
        id=chapter_id,
        study_id=study_node.id,
        title="Chapter 1",
        order=0,
        white=None,
        black=None,
        event="Chapter 1",
        date=None,
        result="*",
        r2_key=r2_key,
        pgn_hash="seed",
        pgn_size=1,
        pgn_status="ready",
        r2_etag="seed-etag",
        last_synced_at=datetime.now(timezone.utc),
        tree_revision=1,
        tree_updated_at=datetime.now(timezone.utc),
    )
    session.add(chapter)
    await acl_repo.create_acl(
        ACL(
            id=f"acl-{permission.value}",
            object_id=study_node.id,
            user_id="shared-1",
            permission=permission,
            inherit_to_children=True,
            is_inherited=False,
            inherited_from=None,
            granted_by="owner-1",
        )
    )
    await session.commit()
    return study_node.id, chapter_id, fake_r2


def _tree_payload() -> dict:
    return {
        "version": "v1",
        "rootId": "root",
        "nodes": {
            "root": {
                "id": "root",
                "parentId": None,
                "san": "",
                "children": ["n1"],
                "comment": None,
                "nags": [],
            },
            "n1": {
                "id": "n1",
                "parentId": "root",
                "san": "e4",
                "children": [],
                "comment": None,
                "nags": [],
            },
        },
        "meta": {"result": "*"},
    }


@pytest.mark.asyncio
async def test_viewer_cannot_save_chapter_tree(app, session, node_service, acl_repo, monkeypatch):
    """A viewer can read a study but cannot save the chapter tree."""
    _study_id, chapter_id, fake_r2 = await _seed_shared_study(
        session,
        node_service,
        acl_repo,
        Permission.VIEWER,
    )
    monkeypatch.setattr(patch_study_api, "create_r2_client_from_env", lambda: fake_r2)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.put(
            f"/studies/study-patch/chapter/{chapter_id}/tree",
            json=_tree_payload(),
            headers={"Authorization": "Bearer shared-1"},
        )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_viewer_can_read_study_chapters_and_tree_metadata(app, session, node_service, acl_repo, monkeypatch):
    """A viewer can read study/chapter metadata but remains read-only."""
    study_id, chapter_id, fake_r2 = await _seed_shared_study(
        session,
        node_service,
        acl_repo,
        Permission.VIEWER,
    )
    monkeypatch.setattr(patch_study_api, "create_r2_client_from_env", lambda: fake_r2)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        study_response = await client.get(
            f"/studies/{study_id}",
            headers={"Authorization": "Bearer shared-1"},
        )
        chapters_response = await client.get(
            f"/studies/{study_id}/chapters",
            headers={"Authorization": "Bearer shared-1"},
        )
        meta_response = await client.get(
            f"/studies/study-patch/chapter/{chapter_id}/tree-meta",
            headers={"Authorization": "Bearer shared-1"},
        )

    assert study_response.status_code == 200
    assert study_response.json()["study"]["effective_permission"] == "viewer"
    assert study_response.json()["study"]["can_edit"] is False
    assert chapters_response.status_code == 200
    assert chapters_response.json()[0]["id"] == chapter_id
    assert meta_response.status_code == 200
    assert meta_response.json()["success"] is True
    assert meta_response.json()["tree_revision"] == 1


@pytest.mark.asyncio
async def test_editor_can_save_chapter_tree_and_advances_revision(app, session, node_service, acl_repo, monkeypatch):
    """An editor can save a tree and receives the next tree revision."""
    _study_id, chapter_id, fake_r2 = await _seed_shared_study(
        session,
        node_service,
        acl_repo,
        Permission.EDITOR,
    )
    monkeypatch.setattr(patch_study_api, "create_r2_client_from_env", lambda: fake_r2)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.put(
            f"/studies/study-patch/chapter/{chapter_id}/tree",
            json=_tree_payload(),
            headers={"Authorization": "Bearer shared-1"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["tree_revision"] == 2
