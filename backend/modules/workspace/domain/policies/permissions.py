from workspace.domain.models.types import Permission
from workspace.domain.policies.discussion_permissions import (
    DiscussionPermissionError,
    require_admin_access,
    require_commenter_access,
    require_editor_access,
)
from workspace.domain.policies.permissions_core import PermissionPolicy
from workspace.domain.policies.permissions_inheritance import InheritancePolicy


def _node_to_model(node):
    """Convert ORM node to domain model for permission checks."""
    from workspace.domain.models.node import NodeModel
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
    from workspace.domain.models.acl import ACLModel
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
