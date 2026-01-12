"""
API tests for Phase 3 variation tree editing endpoints.

Tests the following endpoints:
- POST /studies/{id}/chapters/{cid}/moves
- DELETE /studies/{id}/chapters/{cid}/moves/{move_id}
- POST /studies/{id}/chapters/{cid}/variations
- POST /studies/{id}/chapters/{cid}/moves/{move_id}/annotations
- PUT /studies/{id}/chapters/{cid}/variations/{vid}/promote
"""

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from ulid import ULID

from workspace.api.router import api_router
from workspace.db.tables.variations import VariationPriority, VariationVisibility


@pytest.fixture
def app() -> FastAPI:
    """Create FastAPI app for testing."""
    app = FastAPI()
    app.include_router(api_router)
    return app


# ============================================================================
# POST /studies/{id}/chapters/{cid}/moves Tests
# ============================================================================


@pytest.mark.asyncio
async def test_add_move_success(app: FastAPI, variation_repo, session):
    """Test adding a move successfully returns 201 and ETag header."""
    study_id = str(ULID())
    chapter_id = str(ULID())

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            f"/studies/{study_id}/chapters/{chapter_id}/moves",
            json={
                "san": "e4",
                "uci": "e2e4",
                "fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
                "move_number": 1,
                "color": "white",
                "rank": 0,
            },
            headers={"Authorization": "Bearer user123"},
        )

    assert response.status_code == 201
    data = response.json()
    assert data["san"] == "e4"
    assert data["rank"] == 0
    assert "version" in data

    # Check ETag header is present
    assert "etag" in response.headers
    assert response.headers["etag"] == f'"{data["version"]}"'


@pytest.mark.asyncio
async def test_add_move_parent_not_found(app: FastAPI, session):
    """Test adding move with non-existent parent returns 404."""
    study_id = str(ULID())
    chapter_id = str(ULID())
    parent_id = str(ULID())

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            f"/studies/{study_id}/chapters/{chapter_id}/moves",
            json={
                "parent_id": parent_id,
                "san": "e5",
                "uci": "e7e5",
                "fen": "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2",
                "move_number": 1,
                "color": "black",
                "rank": 0,
            },
            headers={"Authorization": "Bearer user123"},
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_add_move_with_parent(app: FastAPI, variation_repo, session):
    """Test adding move as child of existing move."""
    study_id = str(ULID())
    chapter_id = str(ULID())

    # Create parent move first
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        parent_response = await client.post(
            f"/studies/{study_id}/chapters/{chapter_id}/moves",
            json={
                "san": "e4",
                "uci": "e2e4",
                "fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
                "move_number": 1,
                "color": "white",
                "rank": 0,
            },
            headers={"Authorization": "Bearer user123"},
        )
        parent_id = parent_response.json()["id"]

        # Add child move
        response = await client.post(
            f"/studies/{study_id}/chapters/{chapter_id}/moves",
            json={
                "parent_id": parent_id,
                "san": "e5",
                "uci": "e7e5",
                "fen": "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2",
                "move_number": 1,
                "color": "black",
                "rank": 0,
            },
            headers={"Authorization": "Bearer user123"},
        )

    assert response.status_code == 201
    data = response.json()
    assert data["parent_id"] == parent_id


# ============================================================================
# DELETE /studies/{id}/chapters/{cid}/moves/{move_id} Tests
# ============================================================================


@pytest.mark.asyncio
async def test_delete_move_success(app: FastAPI, variation_repo, session):
    """Test deleting a move returns 204."""
    study_id = str(ULID())
    chapter_id = str(ULID())

    # Create move first
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        create_response = await client.post(
            f"/studies/{study_id}/chapters/{chapter_id}/moves",
            json={
                "san": "e4",
                "uci": "e2e4",
                "fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
                "move_number": 1,
                "color": "white",
                "rank": 0,
            },
            headers={"Authorization": "Bearer user123"},
        )
        move_id = create_response.json()["id"]

        # Delete move
        response = await client.delete(
            f"/studies/{study_id}/chapters/{chapter_id}/moves/{move_id}",
            headers={"Authorization": "Bearer user123"},
        )

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_move_not_found(app: FastAPI, session):
    """Test deleting non-existent move returns 404."""
    study_id = str(ULID())
    chapter_id = str(ULID())
    move_id = str(ULID())

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.delete(
            f"/studies/{study_id}/chapters/{chapter_id}/moves/{move_id}",
            headers={"Authorization": "Bearer user123"},
        )

    assert response.status_code == 404


# ============================================================================
# POST /studies/{id}/chapters/{cid}/variations Tests
# ============================================================================


@pytest.mark.asyncio
async def test_add_variation_success(app: FastAPI, variation_repo, session):
    """Test adding a variation successfully returns 201 and ETag."""
    study_id = str(ULID())
    chapter_id = str(ULID())

    # Create main line move first
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        parent_response = await client.post(
            f"/studies/{study_id}/chapters/{chapter_id}/moves",
            json={
                "san": "e4",
                "uci": "e2e4",
                "fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
                "move_number": 1,
                "color": "white",
                "rank": 0,
            },
            headers={"Authorization": "Bearer user123"},
        )
        parent_id = parent_response.json()["id"]

        # Add variation (alternative to e4)
        response = await client.post(
            f"/studies/{study_id}/chapters/{chapter_id}/variations",
            json={
                "san": "d4",
                "uci": "d2d4",
                "fen": "rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq d3 0 1",
                "move_number": 1,
                "color": "white",
                "rank": 1,
            },
            headers={"Authorization": "Bearer user123"},
        )

    assert response.status_code == 201
    data = response.json()
    assert data["san"] == "d4"
    assert data["rank"] == 1

    # Check ETag header
    assert "etag" in response.headers


@pytest.mark.asyncio
async def test_add_variation_rank_zero_validation(app: FastAPI, session):
    """Test adding variation with rank=0 returns 400."""
    study_id = str(ULID())
    chapter_id = str(ULID())

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            f"/studies/{study_id}/chapters/{chapter_id}/variations",
            json={
                "san": "e4",
                "uci": "e2e4",
                "fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
                "move_number": 1,
                "color": "white",
                "rank": 0,  # Invalid - variations must have rank > 0
            },
            headers={"Authorization": "Bearer user123"},
        )

    assert response.status_code == 400
    assert "rank > 0" in response.json()["detail"].lower()


# ============================================================================
# POST /studies/{id}/chapters/{cid}/moves/{move_id}/annotations Tests
# ============================================================================


@pytest.mark.asyncio
async def test_add_annotation_success(app: FastAPI, variation_repo, session):
    """Test adding annotation successfully returns 201 and ETag."""
    study_id = str(ULID())
    chapter_id = str(ULID())

    # Create move first
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        move_response = await client.post(
            f"/studies/{study_id}/chapters/{chapter_id}/moves",
            json={
                "san": "e4",
                "uci": "e2e4",
                "fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
                "move_number": 1,
                "color": "white",
                "rank": 0,
            },
            headers={"Authorization": "Bearer user123"},
        )
        move_id = move_response.json()["id"]

        # Add annotation
        response = await client.post(
            f"/studies/{study_id}/chapters/{chapter_id}/moves/{move_id}/annotations",
            json={
                "nag": "!!",
                "text": "Brilliant opening move",
            },
            headers={"Authorization": "Bearer user123"},
        )

    assert response.status_code == 201
    data = response.json()
    assert data["move_id"] == move_id
    assert data["nag"] == "!!"
    assert data["text"] == "Brilliant opening move"

    # Check ETag header
    assert "etag" in response.headers


@pytest.mark.asyncio
async def test_add_annotation_move_not_found(app: FastAPI, session):
    """Test adding annotation to non-existent move returns 404."""
    study_id = str(ULID())
    chapter_id = str(ULID())
    move_id = str(ULID())

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            f"/studies/{study_id}/chapters/{chapter_id}/moves/{move_id}/annotations",
            json={
                "nag": "?",
                "text": "Questionable move",
            },
            headers={"Authorization": "Bearer user123"},
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_add_annotation_already_exists(app: FastAPI, variation_repo, session):
    """Test adding annotation when one already exists returns 409."""
    study_id = str(ULID())
    chapter_id = str(ULID())

    # Create move and annotation
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        move_response = await client.post(
            f"/studies/{study_id}/chapters/{chapter_id}/moves",
            json={
                "san": "e4",
                "uci": "e2e4",
                "fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
                "move_number": 1,
                "color": "white",
                "rank": 0,
            },
            headers={"Authorization": "Bearer user123"},
        )
        move_id = move_response.json()["id"]

        # Add first annotation
        await client.post(
            f"/studies/{study_id}/chapters/{chapter_id}/moves/{move_id}/annotations",
            json={"nag": "!", "text": "Good move"},
            headers={"Authorization": "Bearer user123"},
        )

        # Try to add second annotation - should fail
        response = await client.post(
            f"/studies/{study_id}/chapters/{chapter_id}/moves/{move_id}/annotations",
            json={"nag": "!!", "text": "Excellent move"},
            headers={"Authorization": "Bearer user123"},
        )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_add_annotation_nag_only(app: FastAPI, variation_repo, session):
    """Test adding annotation with only NAG symbol."""
    study_id = str(ULID())
    chapter_id = str(ULID())

    # Create move first
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        move_response = await client.post(
            f"/studies/{study_id}/chapters/{chapter_id}/moves",
            json={
                "san": "e4",
                "uci": "e2e4",
                "fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
                "move_number": 1,
                "color": "white",
                "rank": 0,
            },
            headers={"Authorization": "Bearer user123"},
        )
        move_id = move_response.json()["id"]

        # Add annotation with only NAG
        response = await client.post(
            f"/studies/{study_id}/chapters/{chapter_id}/moves/{move_id}/annotations",
            json={"nag": "?!"},
            headers={"Authorization": "Bearer user123"},
        )

    assert response.status_code == 201
    data = response.json()
    assert data["nag"] == "?!"
    assert data["text"] is None


# ============================================================================
# PUT /studies/{id}/chapters/{cid}/variations/{vid}/promote Tests
# ============================================================================


@pytest.mark.asyncio
async def test_promote_variation_success(app: FastAPI, variation_repo, session):
    """Test promoting a variation to main line returns 204."""
    study_id = str(ULID())
    chapter_id = str(ULID())

    # Create main line and variation
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create e4 (main line)
        main_response = await client.post(
            f"/studies/{study_id}/chapters/{chapter_id}/moves",
            json={
                "san": "e4",
                "uci": "e2e4",
                "fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
                "move_number": 1,
                "color": "white",
                "rank": 0,
            },
            headers={"Authorization": "Bearer user123"},
        )

        # Create d4 (variation)
        var_response = await client.post(
            f"/studies/{study_id}/chapters/{chapter_id}/variations",
            json={
                "san": "d4",
                "uci": "d2d4",
                "fen": "rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq d3 0 1",
                "move_number": 1,
                "color": "white",
                "rank": 1,
            },
            headers={"Authorization": "Bearer user123"},
        )
        variation_id = var_response.json()["id"]

        # Promote d4 to main line
        response = await client.put(
            f"/studies/{study_id}/chapters/{chapter_id}/variations/{variation_id}/promote",
            json={},
            headers={"Authorization": "Bearer user123"},
        )

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_promote_variation_not_found(app: FastAPI, session):
    """Test promoting non-existent variation returns 404."""
    study_id = str(ULID())
    chapter_id = str(ULID())
    variation_id = str(ULID())

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.put(
            f"/studies/{study_id}/chapters/{chapter_id}/variations/{variation_id}/promote",
            json={},
            headers={"Authorization": "Bearer user123"},
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_promote_variation_optimistic_lock(app: FastAPI, variation_repo, session):
    """Test promoting variation with stale version returns 409."""
    study_id = str(ULID())
    chapter_id = str(ULID())

    # Create variation
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create main line
        await client.post(
            f"/studies/{study_id}/chapters/{chapter_id}/moves",
            json={
                "san": "e4",
                "uci": "e2e4",
                "fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
                "move_number": 1,
                "color": "white",
                "rank": 0,
            },
            headers={"Authorization": "Bearer user123"},
        )

        # Create variation
        var_response = await client.post(
            f"/studies/{study_id}/chapters/{chapter_id}/variations",
            json={
                "san": "d4",
                "uci": "d2d4",
                "fen": "rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq d3 0 1",
                "move_number": 1,
                "color": "white",
                "rank": 1,
            },
            headers={"Authorization": "Bearer user123"},
        )
        variation_id = var_response.json()["id"]

        # Try to promote with wrong expected_version
        response = await client.put(
            f"/studies/{study_id}/chapters/{chapter_id}/variations/{variation_id}/promote",
            json={"expected_version": 999},  # Wrong version
            headers={"Authorization": "Bearer user123"},
        )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_promote_variation_if_match_header(app: FastAPI, variation_repo, session):
    """Test promoting variation using If-Match header."""
    study_id = str(ULID())
    chapter_id = str(ULID())

    # Create variation
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create main line
        await client.post(
            f"/studies/{study_id}/chapters/{chapter_id}/moves",
            json={
                "san": "e4",
                "uci": "e2e4",
                "fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
                "move_number": 1,
                "color": "white",
                "rank": 0,
            },
            headers={"Authorization": "Bearer user123"},
        )

        # Create variation
        var_response = await client.post(
            f"/studies/{study_id}/chapters/{chapter_id}/variations",
            json={
                "san": "d4",
                "uci": "d2d4",
                "fen": "rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq d3 0 1",
                "move_number": 1,
                "color": "white",
                "rank": 1,
            },
            headers={"Authorization": "Bearer user123"},
        )
        variation_id = var_response.json()["id"]
        version = var_response.json()["version"]

        # Promote using If-Match header
        response = await client.put(
            f"/studies/{study_id}/chapters/{chapter_id}/variations/{variation_id}/promote",
            json={},
            headers={
                "Authorization": "Bearer user123",
                "If-Match": f'"{version}"',
            },
        )

    assert response.status_code == 204
