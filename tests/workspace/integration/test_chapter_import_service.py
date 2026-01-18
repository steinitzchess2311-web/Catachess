"""
Integration tests for ChapterImportService.

Tests the complete workflow of importing PGN files into studies.
"""

import pytest

from workspace.domain.models.node import CreateNodeCommand
from workspace.domain.models.study import ImportPGNCommand
from workspace.domain.models.types import NodeType, Visibility
from workspace.domain.services.chapter_import_service import ChapterImportService, ChapterImportError
from workspace.domain.services.node_service import NodeService


# Sample PGN with 3 games
SAMPLE_PGN_3_GAMES = """
[Event "Test Tournament 1"]
[Site "Online"]
[Date "2024.01.01"]
[Round "1"]
[White "Player A"]
[Black "Player B"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 1-0

[Event "Test Tournament 2"]
[Site "Online"]
[Date "2024.01.02"]
[Round "2"]
[White "Player C"]
[Black "Player D"]
[Result "0-1"]

1. d4 d5 2. c4 e6 3. Nc3 Nf6 0-1

[Event "Test Tournament 3"]
[Site "Online"]
[Date "2024.01.03"]
[Round "3"]
[White "Player E"]
[Black "Player F"]
[Result "1/2-1/2"]

1. c4 c5 2. Nc3 Nc6 3. Nf3 Nf6 1/2-1/2
"""

NO_HEADER_PGN = "1. e4 e5 2. Nf3 Nc6 3. Bb5 1-0"


@pytest.mark.asyncio
async def test_import_single_study(
    chapter_import_service: ChapterImportService,
    node_service: NodeService,
    study_repo,
    mock_r2_client,
):
    """Test importing PGN with <= 64 chapters creates single study."""
    # Create workspace as parent
    workspace = await node_service.create_node(
        CreateNodeCommand(
            node_type=NodeType.WORKSPACE,
            title="Test Workspace",
            owner_id="user123",
        ),
        actor_id="user123",
    )

    # Import PGN
    command = ImportPGNCommand(
        parent_id=workspace.id,
        owner_id="user123",
        pgn_content=SAMPLE_PGN_3_GAMES,
        base_title="Test Study",
        auto_split=True,
        visibility=Visibility.PRIVATE,
    )

    result = await chapter_import_service.import_pgn(command, actor_id="user123")

    # Verify result
    assert result.total_chapters == 3
    assert result.single_study is True
    assert result.was_split is False
    assert len(result.studies_created) == 1
    assert result.folder_id is None

    # Verify study was created
    study_id = result.studies_created[0]
    study = await study_repo.get_study_by_id(study_id)
    assert study is not None
    assert study.chapter_count == 3

    # Verify chapters were created
    chapters = await study_repo.get_chapters_for_study(study_id)
    assert len(chapters) == 3

    # Verify chapter metadata
    chapter1 = chapters[0]
    assert chapter1.title == "Test Tournament 1"
    assert chapter1.white == "Player A"
    assert chapter1.black == "Player B"
    assert chapter1.result == "1-0"
    assert chapter1.order == 0
    assert chapter1.r2_key is not None
    assert chapter1.pgn_hash is not None

    # Verify PGN was uploaded to R2
    assert mock_r2_client.upload_count == 3
    for chapter in chapters:
        assert mock_r2_client.object_exists(chapter.r2_key)


@pytest.mark.asyncio
async def test_import_preserves_chapter_order(
    chapter_import_service: ChapterImportService,
    node_service: NodeService,
    study_repo,
):
    """Test that chapters are imported in correct order."""
    workspace = await node_service.create_node(
        CreateNodeCommand(
            node_type=NodeType.WORKSPACE,
            title="Test Workspace",
            owner_id="user123",
        ),
        actor_id="user123",
    )

    command = ImportPGNCommand(
        parent_id=workspace.id,
        owner_id="user123",
        pgn_content=SAMPLE_PGN_3_GAMES,
        base_title="Order Test",
        auto_split=True,
        visibility=Visibility.PRIVATE,
    )

    result = await chapter_import_service.import_pgn(command, actor_id="user123")
    study_id = result.studies_created[0]
    chapters = await study_repo.get_chapters_for_study(study_id)

    # Verify order
    assert chapters[0].order == 0
    assert chapters[0].title == "Test Tournament 1"
    assert chapters[1].order == 1
    assert chapters[1].title == "Test Tournament 2"
    assert chapters[2].order == 2
    assert chapters[2].title == "Test Tournament 3"


@pytest.mark.asyncio
async def test_import_under_folder(
    chapter_import_service: ChapterImportService,
    node_service: NodeService,
    study_repo,
):
    """Test importing study under a folder."""
    # Create workspace and folder
    workspace = await node_service.create_node(
        CreateNodeCommand(
            node_type=NodeType.WORKSPACE,
            title="Test Workspace",
            owner_id="user123",
        ),
        actor_id="user123",
    )

    folder = await node_service.create_node(
        CreateNodeCommand(
            node_type=NodeType.FOLDER,
            title="My Folder",
            owner_id="user123",
            parent_id=workspace.id,
        ),
        actor_id="user123",
    )

    # Import under folder
    command = ImportPGNCommand(
        parent_id=folder.id,
        owner_id="user123",
        pgn_content=SAMPLE_PGN_3_GAMES,
        base_title="Folder Study",
        auto_split=True,
        visibility=Visibility.PRIVATE,
    )

    result = await chapter_import_service.import_pgn(command, actor_id="user123")
    study_id = result.studies_created[0]

    # Verify study is under folder
    study_node = await node_service.get_node(study_id, actor_id="user123")
    assert study_node.parent_id == folder.id
    assert study_node.path.startswith(folder.path)
    assert study_node.depth == folder.depth + 1


@pytest.mark.asyncio
async def test_import_multi_study_auto_split(
    chapter_import_service: ChapterImportService,
    node_service: NodeService,
    study_repo,
    mock_r2_client,
):
    """Test importing PGN with > 64 chapters creates multiple studies."""
    workspace = await node_service.create_node(
        CreateNodeCommand(
            node_type=NodeType.WORKSPACE,
            title="Test Workspace",
            owner_id="user123",
        ),
        actor_id="user123",
    )

    # Generate PGN with 100 games
    games = []
    for i in range(100):
        game = f"""
[Event "Game {i+1}"]
[Site "Online"]
[Date "2024.01.{(i % 28) + 1:02d}"]
[Round "{i+1}"]
[White "Player A"]
[Black "Player B"]
[Result "1-0"]

1. e4 e5 2. Nf3 1-0
"""
        games.append(game)

    large_pgn = "\n".join(games)

    # Import with auto_split
    command = ImportPGNCommand(
        parent_id=workspace.id,
        owner_id="user123",
        pgn_content=large_pgn,
        base_title="Large Study",
        auto_split=True,
        visibility=Visibility.PRIVATE,
    )

    result = await chapter_import_service.import_pgn(command, actor_id="user123")

    # Verify result
    assert result.total_chapters == 100
    assert result.single_study is False
    assert result.was_split is True
    assert len(result.studies_created) == 2  # 100 games -> 2 studies
    assert result.folder_id is not None

    # Verify folder was created
    folder = await node_service.get_node(result.folder_id, actor_id="user123")
    assert folder.node_type == NodeType.FOLDER
    assert "Large Study" in folder.title

    # Verify studies were created under folder
    for study_id in result.studies_created:
        study = await study_repo.get_study_by_id(study_id)
        assert study is not None

        study_node = await node_service.get_node(study_id, actor_id="user123")
        assert study_node.parent_id == result.folder_id

    # Verify chapter distribution
    study1 = await study_repo.get_study_by_id(result.studies_created[0])
    study2 = await study_repo.get_study_by_id(result.studies_created[1])
    assert study1.chapter_count + study2.chapter_count == 100
    # Should be evenly distributed: 50 + 50
    assert abs(study1.chapter_count - study2.chapter_count) <= 1

    # Verify all chapters uploaded to R2
    assert mock_r2_client.upload_count == 100


@pytest.mark.asyncio
async def test_import_exactly_64_chapters(
    chapter_import_service: ChapterImportService,
    node_service: NodeService,
    study_repo,
):
    """Test that exactly 64 chapters creates single study (boundary case)."""
    workspace = await node_service.create_node(
        CreateNodeCommand(
            node_type=NodeType.WORKSPACE,
            title="Test Workspace",
            owner_id="user123",
        ),
        actor_id="user123",
    )

    # Generate PGN with exactly 64 games
    games = []
    for i in range(64):
        game = f"""
[Event "Game {i+1}"]
[Site "Online"]
[Date "2024.01.01"]
[Round "{i+1}"]
[White "Player A"]
[Black "Player B"]
[Result "1-0"]

1. e4 e5 1-0
"""
        games.append(game)

    pgn_64 = "\n".join(games)

    command = ImportPGNCommand(
        parent_id=workspace.id,
        owner_id="user123",
        pgn_content=pgn_64,
        base_title="Exactly 64",
        auto_split=True,
        visibility=Visibility.PRIVATE,
    )

    result = await chapter_import_service.import_pgn(command, actor_id="user123")

    # Should create single study (not split)
    assert result.total_chapters == 64
    assert result.single_study is True
    assert result.was_split is False
    assert len(result.studies_created) == 1
    assert result.folder_id is None


@pytest.mark.asyncio
async def test_import_65_chapters_splits(
    chapter_import_service: ChapterImportService,
    node_service: NodeService,
    study_repo,
):
    """Test that 65 chapters triggers auto-split (boundary case)."""
    workspace = await node_service.create_node(
        CreateNodeCommand(
            node_type=NodeType.WORKSPACE,
            title="Test Workspace",
            owner_id="user123",
        ),
        actor_id="user123",
    )

    # Generate PGN with 65 games
    games = []
    for i in range(65):
        game = f"""
[Event "Game {i+1}"]
[Site "Online"]
[Date "2024.01.01"]
[Round "{i+1}"]
[White "Player A"]
[Black "Player B"]
[Result "1-0"]

1. e4 e5 1-0
"""
        games.append(game)

    pgn_65 = "\n".join(games)

    command = ImportPGNCommand(
        parent_id=workspace.id,
        owner_id="user123",
        pgn_content=pgn_65,
        base_title="Just Over Limit",
        auto_split=True,
        visibility=Visibility.PRIVATE,
    )

    result = await chapter_import_service.import_pgn(command, actor_id="user123")

    # Should split into 2 studies
    assert result.total_chapters == 65
    assert result.single_study is False
    assert result.was_split is True
    assert len(result.studies_created) == 2
    assert result.folder_id is not None


@pytest.mark.asyncio
async def test_import_with_public_visibility(
    chapter_import_service: ChapterImportService,
    node_service: NodeService,
    study_repo,
):
    """Test importing with public visibility."""
    workspace = await node_service.create_node(
        CreateNodeCommand(
            node_type=NodeType.WORKSPACE,
            title="Test Workspace",
            owner_id="user123",
        ),
        actor_id="user123",
    )

    command = ImportPGNCommand(
        parent_id=workspace.id,
        owner_id="user123",
        pgn_content=SAMPLE_PGN_3_GAMES,
        base_title="Public Study",
        auto_split=True,
        visibility=Visibility.PUBLIC,
    )

    result = await chapter_import_service.import_pgn(command, actor_id="user123")
    study_id = result.studies_created[0]

    # Verify study has public visibility
    study_node = await node_service.get_node(study_id, actor_id="user123")
    assert study_node.visibility == Visibility.PUBLIC


@pytest.mark.asyncio
async def test_import_pgn_content_integrity(
    chapter_import_service: ChapterImportService,
    node_service: NodeService,
    study_repo,
    mock_r2_client,
):
    """Test that PGN content is correctly stored and retrievable."""
    workspace = await node_service.create_node(
        CreateNodeCommand(
            node_type=NodeType.WORKSPACE,
            title="Test Workspace",
            owner_id="user123",
        ),
        actor_id="user123",
    )

    command = ImportPGNCommand(
        parent_id=workspace.id,
        owner_id="user123",
        pgn_content=SAMPLE_PGN_3_GAMES,
        base_title="Integrity Test",
        auto_split=True,
        visibility=Visibility.PRIVATE,
    )

    result = await chapter_import_service.import_pgn(command, actor_id="user123")
    study_id = result.studies_created[0]
    chapters = await study_repo.get_chapters_for_study(study_id)

    # Verify we can retrieve PGN from R2
    for chapter in chapters:
        pgn_content = mock_r2_client.download_pgn(chapter.r2_key)
        assert pgn_content is not None
        assert len(pgn_content) > 0
        # PGN should contain the moves
        assert "1. e4" in pgn_content or "1. d4" in pgn_content or "1. c4" in pgn_content


@pytest.mark.asyncio
async def test_import_chapter_metadata_extraction(
    chapter_import_service: ChapterImportService,
    node_service: NodeService,
    study_repo,
):
    """Test that chapter metadata is correctly extracted from PGN headers."""
    workspace = await node_service.create_node(
        CreateNodeCommand(
            node_type=NodeType.WORKSPACE,
            title="Test Workspace",
            owner_id="user123",
        ),
        actor_id="user123",
    )

    # PGN with specific metadata
    pgn_with_metadata = """
[Event "World Championship"]
[Site "London"]
[Date "2024.12.25"]
[Round "5"]
[White "Magnus Carlsen"]
[Black "Hikaru Nakamura"]
[Result "1/2-1/2"]

1. d4 Nf6 2. c4 e6 1/2-1/2
"""

    command = ImportPGNCommand(
        parent_id=workspace.id,
        owner_id="user123",
        pgn_content=pgn_with_metadata,
        base_title="Metadata Test",
        auto_split=True,
        visibility=Visibility.PRIVATE,
    )

    result = await chapter_import_service.import_pgn(command, actor_id="user123")
    study_id = result.studies_created[0]
    chapters = await study_repo.get_chapters_for_study(study_id)

    chapter = chapters[0]
    assert chapter.title == "World Championship"
    assert chapter.white == "Magnus Carlsen"
    assert chapter.black == "Hikaru Nakamura"
    assert chapter.event == "World Championship"
    assert chapter.date == "2024.12.25"
    assert chapter.result == "1/2-1/2"


@pytest.mark.asyncio
async def test_import_rejects_missing_headers(
    chapter_import_service: ChapterImportService,
    node_service: NodeService,
):
    """Importing PGN without headers should fail cleanly."""
    workspace = await node_service.create_node(
        CreateNodeCommand(
            node_type=NodeType.WORKSPACE,
            title="Test Workspace",
            owner_id="user123",
        ),
        actor_id="user123",
    )

    command = ImportPGNCommand(
        parent_id=workspace.id,
        owner_id="user123",
        pgn_content=NO_HEADER_PGN,
        base_title="No Headers",
        auto_split=True,
        visibility=Visibility.PRIVATE,
    )

    with pytest.raises(ChapterImportError, match="No games found"):
        await chapter_import_service.import_pgn(command, actor_id="user123")
