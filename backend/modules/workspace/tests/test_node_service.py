"""
Tests for NodeService.
"""

import pytest

from workspace.domain.models.node import CreateNodeCommand, DeleteNodeCommand, MoveNodeCommand, UpdateNodeCommand
from workspace.domain.models.types import NodeType, Permission, Visibility
from workspace.domain.services.node_service import (
    InvalidOperationError,
    NodeNotFoundError,
    NodeService,
    OptimisticLockError,
    PermissionDeniedError,
)


@pytest.mark.asyncio
async def test_create_workspace(node_service: NodeService):
    """Test creating a workspace."""
    command = CreateNodeCommand(
        node_type=NodeType.WORKSPACE,
        title="My Workspace",
        owner_id="user123",
    )

    node = await node_service.create_node(command, actor_id="user123")

    assert node.id is not None
    assert node.node_type == NodeType.WORKSPACE
    assert node.title == "My Workspace"
    assert node.owner_id == "user123"
    assert node.parent_id is None
    assert node.path == f"/{node.id}/"
    assert node.depth == 0
    assert node.version == 1


@pytest.mark.asyncio
async def test_create_folder_under_workspace(node_service: NodeService):
    """Test creating a folder under workspace."""
    # Create workspace
    workspace = await node_service.create_node(
        CreateNodeCommand(
            node_type=NodeType.WORKSPACE,
            title="Workspace",
            owner_id="user123",
        ),
        actor_id="user123",
    )

    # Create folder
    folder = await node_service.create_node(
        CreateNodeCommand(
            node_type=NodeType.FOLDER,
            title="My Folder",
            owner_id="user123",
            parent_id=workspace.id,
        ),
        actor_id="user123",
    )

    assert folder.parent_id == workspace.id
    assert folder.path == f"{workspace.path}{folder.id}/"
    assert folder.depth == 1


@pytest.mark.asyncio
async def test_create_study_under_folder(node_service: NodeService):
    """Test creating a study under folder."""
    # Create workspace
    workspace = await node_service.create_node(
        CreateNodeCommand(
            node_type=NodeType.WORKSPACE,
            title="Workspace",
            owner_id="user123",
        ),
        actor_id="user123",
    )

    # Create folder
    folder = await node_service.create_node(
        CreateNodeCommand(
            node_type=NodeType.FOLDER,
            title="Folder",
            owner_id="user123",
            parent_id=workspace.id,
        ),
        actor_id="user123",
    )

    # Create study
    study = await node_service.create_node(
        CreateNodeCommand(
            node_type=NodeType.STUDY,
            title="My Study",
            owner_id="user123",
            parent_id=folder.id,
        ),
        actor_id="user123",
    )

    assert study.parent_id == folder.id
    assert study.path == f"{folder.path}{study.id}/"
    assert study.depth == 2


@pytest.mark.asyncio
async def test_update_node_title(node_service: NodeService):
    """Test updating node title."""
    node = await node_service.create_node(
        CreateNodeCommand(
            node_type=NodeType.WORKSPACE,
            title="Original Title",
            owner_id="user123",
        ),
        actor_id="user123",
    )

    updated = await node_service.update_node(
        UpdateNodeCommand(
            node_id=node.id,
            title="New Title",
            version=1,
        ),
        actor_id="user123",
    )

    assert updated.title == "New Title"
    assert updated.version == 2


@pytest.mark.asyncio
async def test_update_node_optimistic_lock(node_service: NodeService):
    """Test optimistic locking on update."""
    node = await node_service.create_node(
        CreateNodeCommand(
            node_type=NodeType.WORKSPACE,
            title="Title",
            owner_id="user123",
        ),
        actor_id="user123",
    )

    # Update with wrong version should fail
    with pytest.raises(OptimisticLockError):
        await node_service.update_node(
            UpdateNodeCommand(
                node_id=node.id,
                title="New Title",
                version=999,  # Wrong version
            ),
            actor_id="user123",
        )


@pytest.mark.asyncio
async def test_move_node(node_service: NodeService):
    """Test moving a node."""
    # Create workspace
    workspace = await node_service.create_node(
        CreateNodeCommand(
            node_type=NodeType.WORKSPACE,
            title="Workspace",
            owner_id="user123",
        ),
        actor_id="user123",
    )

    # Create two folders
    folder1 = await node_service.create_node(
        CreateNodeCommand(
            node_type=NodeType.FOLDER,
            title="Folder 1",
            owner_id="user123",
            parent_id=workspace.id,
        ),
        actor_id="user123",
    )

    folder2 = await node_service.create_node(
        CreateNodeCommand(
            node_type=NodeType.FOLDER,
            title="Folder 2",
            owner_id="user123",
            parent_id=workspace.id,
        ),
        actor_id="user123",
    )

    # Create study under folder1
    study = await node_service.create_node(
        CreateNodeCommand(
            node_type=NodeType.STUDY,
            title="Study",
            owner_id="user123",
            parent_id=folder1.id,
        ),
        actor_id="user123",
    )

    old_path = study.path

    # Move study to folder2
    moved = await node_service.move_node(
        MoveNodeCommand(
            node_id=study.id,
            new_parent_id=folder2.id,
            version=1,
        ),
        actor_id="user123",
    )

    assert moved.parent_id == folder2.id
    assert moved.path == f"{folder2.path}{study.id}/"
    assert moved.path != old_path
    assert moved.version == 2


@pytest.mark.asyncio
async def test_move_node_to_descendant_fails(node_service: NodeService):
    """Test that moving node to its descendant fails."""
    workspace = await node_service.create_node(
        CreateNodeCommand(
            node_type=NodeType.WORKSPACE,
            title="Workspace",
            owner_id="user123",
        ),
        actor_id="user123",
    )

    folder = await node_service.create_node(
        CreateNodeCommand(
            node_type=NodeType.FOLDER,
            title="Folder",
            owner_id="user123",
            parent_id=workspace.id,
        ),
        actor_id="user123",
    )

    # Try to move workspace under folder (its descendant)
    with pytest.raises(InvalidOperationError):
        await node_service.move_node(
            MoveNodeCommand(
                node_id=workspace.id,
                new_parent_id=folder.id,
                version=1,
            ),
            actor_id="user123",
        )


@pytest.mark.asyncio
async def test_delete_node(node_service: NodeService):
    """Test soft deleting a node."""
    node = await node_service.create_node(
        CreateNodeCommand(
            node_type=NodeType.WORKSPACE,
            title="Workspace",
            owner_id="user123",
        ),
        actor_id="user123",
    )

    deleted = await node_service.delete_node(
        DeleteNodeCommand(
            node_id=node.id,
            version=1,
        ),
        actor_id="user123",
    )

    assert deleted.is_deleted is True
    assert deleted.deleted_at is not None
    assert deleted.version == 2


@pytest.mark.asyncio
async def test_restore_node(node_service: NodeService):
    """Test restoring a deleted node."""
    node = await node_service.create_node(
        CreateNodeCommand(
            node_type=NodeType.WORKSPACE,
            title="Workspace",
            owner_id="user123",
        ),
        actor_id="user123",
    )

    # Delete
    await node_service.delete_node(
        DeleteNodeCommand(node_id=node.id, version=1),
        actor_id="user123",
    )

    # Restore
    restored = await node_service.restore_node(node.id, actor_id="user123")

    assert restored.is_deleted is False
    assert restored.deleted_at is None
    assert restored.version == 3


@pytest.mark.asyncio
async def test_get_node_requires_permission(node_service: NodeService):
    """Test that getting a node requires permission."""
    node = await node_service.create_node(
        CreateNodeCommand(
            node_type=NodeType.WORKSPACE,
            title="Workspace",
            owner_id="user123",
        ),
        actor_id="user123",
    )

    # Owner can access
    fetched = await node_service.get_node(node.id, actor_id="user123")
    assert fetched.id == node.id

    # Other user without permission cannot access
    with pytest.raises(PermissionDeniedError):
        await node_service.get_node(node.id, actor_id="user456")


@pytest.mark.asyncio
async def test_get_children(node_service: NodeService):
    """Test getting children of a node."""
    workspace = await node_service.create_node(
        CreateNodeCommand(
            node_type=NodeType.WORKSPACE,
            title="Workspace",
            owner_id="user123",
        ),
        actor_id="user123",
    )

    # Create 3 folders
    for i in range(3):
        await node_service.create_node(
            CreateNodeCommand(
                node_type=NodeType.FOLDER,
                title=f"Folder {i}",
                owner_id="user123",
                parent_id=workspace.id,
            ),
            actor_id="user123",
        )

    children = await node_service.get_children(workspace.id, actor_id="user123")
    assert len(children) == 3


@pytest.mark.asyncio
async def test_node_not_found_error(node_service: NodeService):
    """Test NodeNotFoundError is raised."""
    with pytest.raises(NodeNotFoundError):
        await node_service.get_node("nonexistent", actor_id="user123")
