"""
Unit tests for permission policies.
"""

import pytest
from datetime import datetime

from workspace.domain.models.acl import ACLModel
from workspace.domain.models.node import NodeModel
from workspace.domain.models.types import NodeType, Permission, Visibility
from workspace.domain.policies.permissions import PermissionPolicy


def test_owner_can_read():
    """Test that owner can always read."""
    node = NodeModel(
        id="node1",
        node_type=NodeType.WORKSPACE,
        title="Test",
        owner_id="user1",
        visibility=Visibility.PRIVATE,
        parent_id=None,
        path="/node1/",
        depth=0,
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    assert PermissionPolicy.can_read(node, "user1", None) is True


def test_non_owner_without_acl_cannot_read():
    """Test that non-owner without ACL cannot read."""
    node = NodeModel(
        id="node1",
        node_type=NodeType.WORKSPACE,
        title="Test",
        owner_id="user1",
        visibility=Visibility.PRIVATE,
        parent_id=None,
        path="/node1/",
        depth=0,
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    assert PermissionPolicy.can_read(node, "user2", None) is False


def test_viewer_can_read():
    """Test that viewer can read."""
    node = NodeModel(
        id="node1",
        node_type=NodeType.WORKSPACE,
        title="Test",
        owner_id="user1",
        visibility=Visibility.PRIVATE,
        parent_id=None,
        path="/node1/",
        depth=0,
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    acl = ACLModel(
        id="acl1",
        object_id="node1",
        user_id="user2",
        permission=Permission.VIEWER,
        inherit_to_children=True,
        is_inherited=False,
        inherited_from=None,
        granted_by="user1",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    assert PermissionPolicy.can_read(node, "user2", acl) is True


def test_viewer_cannot_write():
    """Test that viewer cannot write."""
    node = NodeModel(
        id="node1",
        node_type=NodeType.WORKSPACE,
        title="Test",
        owner_id="user1",
        visibility=Visibility.PRIVATE,
        parent_id=None,
        path="/node1/",
        depth=0,
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    acl = ACLModel(
        id="acl1",
        object_id="node1",
        user_id="user2",
        permission=Permission.VIEWER,
        inherit_to_children=True,
        is_inherited=False,
        inherited_from=None,
        granted_by="user1",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    assert PermissionPolicy.can_write(node, "user2", acl) is False


def test_editor_can_write():
    """Test that editor can write."""
    node = NodeModel(
        id="node1",
        node_type=NodeType.WORKSPACE,
        title="Test",
        owner_id="user1",
        visibility=Visibility.PRIVATE,
        parent_id=None,
        path="/node1/",
        depth=0,
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    acl = ACLModel(
        id="acl1",
        object_id="node1",
        user_id="user2",
        permission=Permission.EDITOR,
        inherit_to_children=True,
        is_inherited=False,
        inherited_from=None,
        granted_by="user1",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    assert PermissionPolicy.can_write(node, "user2", acl) is True


def test_editor_cannot_delete():
    """Test that editor cannot delete."""
    node = NodeModel(
        id="node1",
        node_type=NodeType.WORKSPACE,
        title="Test",
        owner_id="user1",
        visibility=Visibility.PRIVATE,
        parent_id=None,
        path="/node1/",
        depth=0,
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    acl = ACLModel(
        id="acl1",
        object_id="node1",
        user_id="user2",
        permission=Permission.EDITOR,
        inherit_to_children=True,
        is_inherited=False,
        inherited_from=None,
        granted_by="user1",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    assert PermissionPolicy.can_delete(node, "user2", acl) is False


def test_admin_can_delete():
    """Test that admin can delete."""
    node = NodeModel(
        id="node1",
        node_type=NodeType.WORKSPACE,
        title="Test",
        owner_id="user1",
        visibility=Visibility.PRIVATE,
        parent_id=None,
        path="/node1/",
        depth=0,
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    acl = ACLModel(
        id="acl1",
        object_id="node1",
        user_id="user2",
        permission=Permission.ADMIN,
        inherit_to_children=True,
        is_inherited=False,
        inherited_from=None,
        granted_by="user1",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    assert PermissionPolicy.can_delete(node, "user2", acl) is True


def test_get_effective_permission():
    """Test getting effective permission level."""
    node = NodeModel(
        id="node1",
        node_type=NodeType.WORKSPACE,
        title="Test",
        owner_id="user1",
        visibility=Visibility.PRIVATE,
        parent_id=None,
        path="/node1/",
        depth=0,
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    # Owner gets owner permission
    assert PermissionPolicy.get_effective_permission(node, "user1", None) == Permission.OWNER

    # User with ACL gets their permission
    acl = ACLModel(
        id="acl1",
        object_id="node1",
        user_id="user2",
        permission=Permission.EDITOR,
        inherit_to_children=True,
        is_inherited=False,
        inherited_from=None,
        granted_by="user1",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    assert PermissionPolicy.get_effective_permission(node, "user2", acl) == Permission.EDITOR

    # User without ACL gets None
    assert PermissionPolicy.get_effective_permission(node, "user3", None) is None
