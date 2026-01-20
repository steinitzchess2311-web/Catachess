import json

import pytest

from backend.core.real_pgn.parser import parse_pgn
from modules.workspace.storage.keys import R2Keys
from patch.backend.study.api import put_chapter_tree
from patch.backend.study.converter import convert_nodetree_to_dto
from patch.backend.study.models import StudyNodeDTO


class MockR2Client:
    def __init__(self) -> None:
        self.storage: dict[str, str] = {}

    def upload_json(self, key: str, content: str, metadata: dict | None = None) -> None:
        self.storage[key] = content

    def download_json(self, key: str) -> str:
        return self.storage[key]

    def exists(self, key: str) -> bool:
        return key in self.storage


@pytest.mark.asyncio
async def test_stage12_import_edit_writeback():
    pgn = (
        '[Event "Stage12"]\n'
        '[Result "*"]\n\n'
        '1. e4 e5 2. Nf3 Nc6 *'
    )

    node_tree = parse_pgn(pgn)
    tree_dto = convert_nodetree_to_dto(node_tree)

    # Edit: append a new move to the first available leaf (non-root) node.
    leaf_id = None
    for node_id, node in tree_dto.nodes.items():
        if node_id == tree_dto.rootId:
            continue
        if node.san in ("", "<root>"):
            continue
        if len(node.children) == 0:
            leaf_id = node_id
            break

    assert leaf_id is not None

    new_id = "stage12-edit-1"
    tree_dto.nodes[new_id] = StudyNodeDTO(
        id=new_id,
        parentId=leaf_id,
        san="Bb5",
        children=[],
        comment=None,
        nags=[],
    )
    tree_dto.nodes[leaf_id].children.append(new_id)

    r2_client = MockR2Client()
    response = await put_chapter_tree("chapter-1", tree_dto, r2_client=r2_client)

    assert response.success is True

    key = R2Keys.chapter_tree_json("chapter-1")
    assert r2_client.exists(key)

    stored = r2_client.download_json(key)
    stored_data = json.loads(stored)

    assert stored_data["rootId"] == "root"
    assert "fen" not in stored
