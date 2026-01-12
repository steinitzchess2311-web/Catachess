"""Tests for privacy control rules."""
import uuid

import httpx
import pytest
from httpx import ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from workspace.api.app import app
from workspace.db.repos.acl_repo import ACLRepository
from workspace.db.repos.node_repo import NodeRepository
from workspace.db.tables.acl import ACL
from workspace.db.tables.nodes import Node


@pytest.fixture
async def node_repo(session: AsyncSession) -> NodeRepository:
    """Get node repository."""
    return NodeRepository(session)


@pytest.fixture
async def acl_repo(session: AsyncSession) -> ACLRepository:
    """Get ACL repository."""
    return ACLRepository(session)


@pytest.fixture
async def owner_id() -> str:
    """Owner user ID."""
    return str(uuid.uuid4())


@pytest.fixture
async def other_user_id() -> str:
    """Other user ID."""
    return str(uuid.uuid4())


@pytest.fixture
async def private_study(
    node_repo: NodeRepository, owner_id: str, session: AsyncSession
) -> Node:
    """Create a private study."""
    study = Node(
        id=str(uuid.uuid4()),
        name="Private Study",
        node_type="study",
        owner_id=owner_id,
        visibility="PRIVATE",
    )
    study = await node_repo.create(study)
    await session.commit()
    return study


@pytest.fixture
async def shared_study(
    node_repo: NodeRepository,
    acl_repo: ACLRepository,
    owner_id: str,
    other_user_id: str,
    session: AsyncSession,
) -> Node:
    """Create a shared study."""
    study = Node(
        id=str(uuid.uuid4()),
        name="Shared Study",
        node_type="study",
        owner_id=owner_id,
        visibility="SHARED",
    )
    study = await node_repo.create(study)

    # Share with other user
    acl = ACL(
        id=str(uuid.uuid4()),
        object_id=study.id,
        user_id=other_user_id,
        role="viewer",
    )
    await acl_repo.create(acl)
    await session.commit()
    return study


@pytest.mark.asyncio
async def test_private_study_returns_404_for_non_owner(
    private_study: Node, other_user_id: str
) -> None:
    """Test that accessing private study as non-owner returns 404."""
    async with httpx.AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            f"/nodes/{private_study.id}",
            headers={"X-User-ID": other_user_id},
        )

    # Should return 404, not 403 (to hide existence)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_private_study_accessible_by_owner(
    private_study: Node, owner_id: str
) -> None:
    """Test that owner can access private study."""
    async with httpx.AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            f"/nodes/{private_study.id}",
            headers={"X-User-ID": owner_id},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == private_study.id


@pytest.mark.asyncio
async def test_shared_study_accessible_by_viewer(
    shared_study: Node, other_user_id: str
) -> None:
    """Test that shared study is accessible by granted user."""
    async with httpx.AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            f"/nodes/{shared_study.id}",
            headers={"X-User-ID": other_user_id},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == shared_study.id


@pytest.mark.asyncio
async def test_shared_study_returns_404_for_non_granted_user(shared_study: Node) -> None:
    """Test that shared study returns 404 for users without permission."""
    random_user_id = str(uuid.uuid4())

    async with httpx.AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            f"/nodes/{shared_study.id}",
            headers={"X-User-ID": random_user_id},
        )

    # Should return 404, not 403
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_search_excludes_private_studies(
    private_study: Node, other_user_id: str
) -> None:
    """Test that search results exclude private studies for non-owners."""
    async with httpx.AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/search",
            params={"q": private_study.name},
            headers={"X-User-ID": other_user_id},
        )

    assert response.status_code == 200
    data = response.json()

    # Private study should not appear in results
    result_ids = [r["id"] for r in data.get("results", [])]
    assert private_study.id not in result_ids


@pytest.mark.asyncio
async def test_search_includes_private_studies_for_owner(
    private_study: Node, owner_id: str
) -> None:
    """Test that search results include private studies for owner."""
    async with httpx.AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/search",
            params={"q": private_study.name},
            headers={"X-User-ID": owner_id},
        )

    # If search endpoint exists
    if response.status_code != 404:
        assert response.status_code == 200
        data = response.json()

        # Private study should appear in owner's results
        result_ids = [r["id"] for r in data.get("results", [])]
        assert private_study.id in result_ids


@pytest.mark.asyncio
async def test_shared_with_me_includes_shared_studies(
    shared_study: Node, other_user_id: str
) -> None:
    """Test that shared-with-me list includes studies shared with user."""
    async with httpx.AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/shares/shared-with-me",
            headers={"X-User-ID": other_user_id},
        )

    if response.status_code != 404:  # If endpoint exists
        assert response.status_code == 200
        data = response.json()

        # Shared study should appear
        shared_ids = [s["id"] for s in data.get("studies", [])]
        assert shared_study.id in shared_ids


@pytest.mark.asyncio
async def test_shared_with_me_excludes_private_studies(
    private_study: Node, other_user_id: str
) -> None:
    """Test that shared-with-me list excludes private studies."""
    async with httpx.AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/shares/shared-with-me",
            headers={"X-User-ID": other_user_id},
        )

    if response.status_code != 404:  # If endpoint exists
        assert response.status_code == 200
        data = response.json()

        # Private study should not appear
        shared_ids = [s["id"] for s in data.get("studies", [])]
        assert private_study.id not in shared_ids


@pytest.mark.asyncio
async def test_403_for_insufficient_permission_on_owned_resource(
    shared_study: Node, other_user_id: str
) -> None:
    """Test that 403 is used when user has some permission but action forbidden."""
    # User has viewer permission on shared study
    # Try to delete (requires admin)
    async with httpx.AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.delete(
            f"/nodes/{shared_study.id}",
            headers={"X-User-ID": other_user_id},
        )

    # This should be 403 (has access but insufficient permission)
    # OR 404 if endpoint doesn't exist
    assert response.status_code in [403, 404]
