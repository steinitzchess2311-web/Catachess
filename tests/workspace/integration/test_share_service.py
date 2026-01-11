"""
Tests for ShareService.
"""

import pytest

from workspace.domain.models.acl import ChangeRoleCommand, CreateShareLinkCommand, RevokeShareCommand, ShareCommand
from workspace.domain.models.node import CreateNodeCommand
from workspace.domain.models.types import NodeType, Permission
from workspace.domain.services.node_service import NodeService, PermissionDeniedError
from workspace.domain.services.share_service import ShareService


@pytest.mark.asyncio
async def test_share_with_user(
    node_service: NodeService, share_service: ShareService
):
    """Test sharing a node with another user."""
    # Create workspace
    workspace = await node_service.create_node(
        CreateNodeCommand(
            node_type=NodeType.WORKSPACE,
            title="Workspace",
            owner_id="user1",
        ),
        actor_id="user1",
    )

    # Share with user2
    acl = await share_service.share_with_user(
        ShareCommand(
            object_id=workspace.id,
            user_id="user2",
            permission=Permission.EDITOR,
            granted_by="user1",
        ),
        actor_id="user1",
    )

    assert acl.object_id == workspace.id
    assert acl.user_id == "user2"
    assert acl.permission == Permission.EDITOR


@pytest.mark.asyncio
async def test_shared_user_can_access_node(
    node_service: NodeService, share_service: ShareService, acl_repo
):
    """Test that shared user can access the node."""
    # Create workspace
    workspace = await node_service.create_node(
        CreateNodeCommand(
            node_type=NodeType.WORKSPACE,
            title="Workspace",
            owner_id="user1",
        ),
        actor_id="user1",
    )

    # Share with user2
    await share_service.share_with_user(
        ShareCommand(
            object_id=workspace.id,
            user_id="user2",
            permission=Permission.VIEWER,
            granted_by="user1",
        ),
        actor_id="user1",
    )

    # User2 should now have access
    has_permission = await acl_repo.check_permission(
        workspace.id, "user2", Permission.VIEWER
    )
    assert has_permission is True


@pytest.mark.asyncio
async def test_revoke_share(
    node_service: NodeService, share_service: ShareService, acl_repo
):
    """Test revoking a user's access."""
    # Create and share workspace
    workspace = await node_service.create_node(
        CreateNodeCommand(
            node_type=NodeType.WORKSPACE,
            title="Workspace",
            owner_id="user1",
        ),
        actor_id="user1",
    )

    await share_service.share_with_user(
        ShareCommand(
            object_id=workspace.id,
            user_id="user2",
            permission=Permission.EDITOR,
            granted_by="user1",
        ),
        actor_id="user1",
    )

    # Verify user2 has access
    has_access = await acl_repo.check_permission(
        workspace.id, "user2", Permission.VIEWER
    )
    assert has_access is True

    # Revoke access
    await share_service.revoke_share(
        RevokeShareCommand(
            object_id=workspace.id,
            user_id="user2",
        ),
        actor_id="user1",
    )

    # Verify user2 no longer has access
    has_access = await acl_repo.check_permission(
        workspace.id, "user2", Permission.VIEWER
    )
    assert has_access is False


@pytest.mark.asyncio
async def test_change_role(
    node_service: NodeService, share_service: ShareService, acl_repo
):
    """Test changing a user's permission level."""
    # Create and share workspace
    workspace = await node_service.create_node(
        CreateNodeCommand(
            node_type=NodeType.WORKSPACE,
            title="Workspace",
            owner_id="user1",
        ),
        actor_id="user1",
    )

    await share_service.share_with_user(
        ShareCommand(
            object_id=workspace.id,
            user_id="user2",
            permission=Permission.VIEWER,
            granted_by="user1",
        ),
        actor_id="user1",
    )

    # Change to editor
    updated_acl = await share_service.change_role(
        ChangeRoleCommand(
            object_id=workspace.id,
            user_id="user2",
            new_permission=Permission.EDITOR,
        ),
        actor_id="user1",
    )

    assert updated_acl.permission == Permission.EDITOR

    # Verify new permission
    has_editor = await acl_repo.check_permission(
        workspace.id, "user2", Permission.EDITOR
    )
    assert has_editor is True


@pytest.mark.asyncio
async def test_create_share_link(
    node_service: NodeService, share_service: ShareService
):
    """Test creating a share link."""
    workspace = await node_service.create_node(
        CreateNodeCommand(
            node_type=NodeType.WORKSPACE,
            title="Workspace",
            owner_id="user1",
        ),
        actor_id="user1",
    )

    link = await share_service.create_share_link(
        CreateShareLinkCommand(
            object_id=workspace.id,
            permission=Permission.VIEWER,
            created_by="user1",
        ),
        actor_id="user1",
    )

    assert link.object_id == workspace.id
    assert link.permission == Permission.VIEWER
    assert link.token is not None
    assert link.is_active is True


@pytest.mark.asyncio
async def test_create_share_link_with_password(
    node_service: NodeService, share_service: ShareService
):
    """Test creating a password-protected share link."""
    workspace = await node_service.create_node(
        CreateNodeCommand(
            node_type=NodeType.WORKSPACE,
            title="Workspace",
            owner_id="user1",
        ),
        actor_id="user1",
    )

    link = await share_service.create_share_link(
        CreateShareLinkCommand(
            object_id=workspace.id,
            permission=Permission.VIEWER,
            created_by="user1",
            password="secret123",
        ),
        actor_id="user1",
    )

    assert link.password_hash is not None

    # Validate correct password
    is_valid = await share_service.validate_share_link_password(link, "secret123")
    assert is_valid is True

    # Validate wrong password
    is_valid = await share_service.validate_share_link_password(link, "wrong")
    assert is_valid is False


@pytest.mark.asyncio
async def test_get_share_link_by_token(
    node_service: NodeService, share_service: ShareService
):
    """Test retrieving share link by token."""
    workspace = await node_service.create_node(
        CreateNodeCommand(
            node_type=NodeType.WORKSPACE,
            title="Workspace",
            owner_id="user1",
        ),
        actor_id="user1",
    )

    created_link = await share_service.create_share_link(
        CreateShareLinkCommand(
            object_id=workspace.id,
            permission=Permission.VIEWER,
            created_by="user1",
        ),
        actor_id="user1",
    )

    # Retrieve by token
    fetched_link = await share_service.get_share_link_by_token(created_link.token)

    assert fetched_link is not None
    assert fetched_link.id == created_link.id
    assert fetched_link.object_id == workspace.id


@pytest.mark.asyncio
async def test_get_shared_with_user(
    node_service: NodeService, share_service: ShareService
):
    """Test getting all nodes shared with a user."""
    # Create multiple workspaces
    ws1 = await node_service.create_node(
        CreateNodeCommand(
            node_type=NodeType.WORKSPACE,
            title="Workspace 1",
            owner_id="user1",
        ),
        actor_id="user1",
    )

    ws2 = await node_service.create_node(
        CreateNodeCommand(
            node_type=NodeType.WORKSPACE,
            title="Workspace 2",
            owner_id="user1",
        ),
        actor_id="user1",
    )

    # Share both with user2
    await share_service.share_with_user(
        ShareCommand(
            object_id=ws1.id,
            user_id="user2",
            permission=Permission.VIEWER,
            granted_by="user1",
        ),
        actor_id="user1",
    )

    await share_service.share_with_user(
        ShareCommand(
            object_id=ws2.id,
            user_id="user2",
            permission=Permission.EDITOR,
            granted_by="user1",
        ),
        actor_id="user1",
    )

    # Get shared nodes
    shared = await share_service.get_shared_with_user("user2")

    assert len(shared) == 2
    node_ids = {node.id for _, node in shared}
    assert ws1.id in node_ids
    assert ws2.id in node_ids


@pytest.mark.asyncio
async def test_non_owner_cannot_share(
    node_service: NodeService, share_service: ShareService
):
    """Test that non-owner without admin permission cannot share."""
    workspace = await node_service.create_node(
        CreateNodeCommand(
            node_type=NodeType.WORKSPACE,
            title="Workspace",
            owner_id="user1",
        ),
        actor_id="user1",
    )

    # user2 tries to share without permission
    with pytest.raises(PermissionDeniedError):
        await share_service.share_with_user(
            ShareCommand(
                object_id=workspace.id,
                user_id="user3",
                permission=Permission.VIEWER,
                granted_by="user2",
            ),
            actor_id="user2",
        )
