"""
Created at: 2026-07-09 01:20 EDT
Created by: Codex
Last Modified at: 2026-07-09 01:20 EDT
Last Modified by: Codex

Permission helpers used by workspace API boundaries. These wrappers convert
ORM records into domain models before delegating to the shared policy core.
"""

from modules.workspace.domain.models.types import Permission
from modules.workspace.domain.policies.discussion_permissions import (
    DiscussionPermissionError,
    require_admin_access,
    require_commenter_access,
    require_editor_access,
)
from modules.workspace.domain.policies.permissions_core import PermissionPolicy
from modules.workspace.domain.policies.permissions_inheritance import InheritancePolicy


def _node_to_model(node):
    """Convert ORM node to domain model for permission checks."""
    from modules.workspace.domain.models.node import NodeModel
    return NodeModel(
        id=node.id,
        node_type=node.node_type,
        title=node.title,
        owner_id=node.owner_id,
        visibility=node.visibility,
        parent_id=node.parent_id,
        path=node.path,
        depth=node.depth,
        version=node.version,
        created_at=node.created_at,
        updated_at=node.updated_at,
        deleted_at=node.deleted_at,
        description=node.description,
        layout=node.layout,
    )


def _acl_to_model(acl):
    """Convert ORM ACL to domain model for permission checks."""
    if acl is None:
        return None
    permission = (
        acl.permission
        if isinstance(acl.permission, Permission)
        else Permission(str(acl.permission))
    )
    from modules.workspace.domain.models.acl import ACLModel
    return ACLModel(
        id=acl.id,
        object_id=acl.object_id,
        user_id=acl.user_id,
        permission=permission,
        inherit_to_children=acl.inherit_to_children,
        is_inherited=acl.is_inherited,
        inherited_from=acl.inherited_from,
        granted_by=acl.granted_by,
        created_at=acl.created_at,
        updated_at=acl.updated_at,
    )


async def can_read(acl_repo, node, user_id: str) -> bool:
    """
    Check read permission for a node.

    Args:
        acl_repo: ACL repository
        node: ORM node instance
        user_id: User ID
    """
    if node is None:
        return False
    acl = await acl_repo.get_acl(node.id, user_id)
    acl_model = _acl_to_model(acl) if acl is not None else None
    return PermissionPolicy.can_read(_node_to_model(node), user_id, acl_model)


async def get_effective_permission(acl_repo, node, user_id: str) -> Permission | None:
    """
    Return the effective ACL permission for a user on a node.

    Owner is represented as Permission.OWNER even when no ACL row exists.
    """
    if node is None:
        return None
    acl = await acl_repo.get_acl(node.id, user_id)
    return PermissionPolicy.get_effective_permission(
        _node_to_model(node),
        user_id,
        _acl_to_model(acl) if acl is not None else None,
    )


async def can_write(acl_repo, node, user_id: str) -> bool:
    """
    Check write permission for a node.

    Product "modifier" access maps to the existing Permission.EDITOR role.
    """
    if node is None:
        return False
    acl = await acl_repo.get_acl(node.id, user_id)
    return PermissionPolicy.can_write(
        _node_to_model(node),
        user_id,
        _acl_to_model(acl) if acl is not None else None,
    )


async def require_node_write_access(acl_repo, node, user_id: str) -> Permission:
    """
    Require editor/admin/owner access and return the effective permission.
    """
    effective = await get_effective_permission(acl_repo, node, user_id)
    if effective is None or not Permission.can_write(effective):
        raise PermissionError("Editor access required")
    return effective


async def check_discussion_permission(
    node_repo,
    acl_repo,
    target_id: str,
    user_id: str,
    required: Permission,
) -> None:
    if required == Permission.COMMENTER:
        await require_commenter_access(node_repo, acl_repo, target_id, user_id)
        return
    if required == Permission.EDITOR:
        await require_editor_access(node_repo, acl_repo, target_id, user_id)
        return
    if required in {Permission.ADMIN, Permission.OWNER}:
        await require_admin_access(node_repo, acl_repo, target_id, user_id)
        return
    raise DiscussionPermissionError("Unsupported permission level")
