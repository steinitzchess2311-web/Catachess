"""
Created at: 2026-07-08 22:15 EDT
Created by: Codex
Last Modified at: 2026-07-08 22:15 EDT
Last Modified by: Codex

Focused backend tests for patch study autosave duplicate upload protection.
"""

import hashlib
from types import SimpleNamespace

import pytest

from patch.backend.study.api import put_chapter_tree
from patch.backend.study.models import StudyNodeDTO, StudyTreeDTO, TreeMetaDTO


class FakeRequest:
    def __init__(self, body: bytes, headers: dict[str, str]) -> None:
        self._body = body
        self.headers = headers

    async def body(self) -> bytes:
        return self._body


class MockR2Client:
    def __init__(self) -> None:
        self.storage: dict[str, str] = {}
        self.metadata: dict[str, dict[str, str]] = {}
        self.upload_count = 0

    def upload_json(self, key: str, content: str, metadata: dict | None = None) -> SimpleNamespace:
        content_bytes = content.encode("utf-8")
        content_hash = hashlib.sha256(content_bytes).hexdigest()
        self.storage[key] = content
        self.metadata[key] = {**(metadata or {}), "content-hash": content_hash}
        self.upload_count += 1
        return SimpleNamespace(size=len(content_bytes), content_hash=content_hash, etag="mock-etag")

    def get_metadata(self, key: str) -> dict[str, str]:
        return self.metadata.get(key, {})


def make_simple_tree(comment: str | None = None) -> StudyTreeDTO:
    return StudyTreeDTO(
        version="v2",
        rootId="root",
        nodes={
            "root": StudyNodeDTO(
                id="root",
                parentId=None,
                san="",
                children=["n1"],
                comment=None,
                nags=[],
            ),
            "n1": StudyNodeDTO(
                id="n1",
                parentId="root",
                san="e4",
                children=[],
                comment=comment,
                nags=[],
            ),
        },
        meta=TreeMetaDTO(result="*"),
    )


def request_for_tree(tree: StudyTreeDTO) -> FakeRequest:
    body = tree.model_dump_json().encode("utf-8")
    tree_hash = hashlib.sha256(body).hexdigest()
    return FakeRequest(body=body, headers={"X-Tree-Hash": tree_hash})


@pytest.mark.asyncio
async def test_put_chapter_tree_skips_duplicate_r2_upload():
    tree = make_simple_tree()
    r2_client = MockR2Client()

    first = await put_chapter_tree("chapter-dedupe", tree, request=request_for_tree(tree), r2_client=r2_client)
    second = await put_chapter_tree("chapter-dedupe", tree, request=request_for_tree(tree), r2_client=r2_client)

    assert first.success is True
    assert second.success is True
    assert r2_client.upload_count == 1


@pytest.mark.asyncio
async def test_put_chapter_tree_uploads_changed_content():
    r2_client = MockR2Client()
    original = make_simple_tree()
    changed = make_simple_tree(comment="New annotation")

    await put_chapter_tree("chapter-changed", original, request=request_for_tree(original), r2_client=r2_client)
    response = await put_chapter_tree("chapter-changed", changed, request=request_for_tree(changed), r2_client=r2_client)

    assert response.success is True
    assert r2_client.upload_count == 2
