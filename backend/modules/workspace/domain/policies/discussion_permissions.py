from workspace.db.repos.acl_repo import ACLRepository
from workspace.db.repos.node_repo import NodeRepository
from workspace.domain.models.types import Permission


class DiscussionPermissionError(Exception):
    pass


async def require_commenter_access(
    node_repo: NodeRepository, acl_repo: ACLRepository, target_id: str, user_id: str
) -> None:
    await _require_permission(node_repo, acl_repo, target_id, user_id, Permission.COMMENTER)


async def require_viewer_access(
    node_repo: NodeRepository, acl_repo: ACLRepository, target_id: str, user_id: str
) -> None:
    await _require_permission(node_repo, acl_repo, target_id, user_id, Permission.VIEWER)


async def require_editor_access(
    node_repo: NodeRepository, acl_repo: ACLRepository, target_id: str, user_id: str
) -> None:
    await _require_permission(node_repo, acl_repo, target_id, user_id, Permission.EDITOR)


async def require_admin_access(
    node_repo: NodeRepository, acl_repo: ACLRepository, target_id: str, user_id: str
) -> None:
    await _require_permission(node_repo, acl_repo, target_id, user_id, Permission.ADMIN)


async def _require_permission(
    node_repo: NodeRepository,
    acl_repo: ACLRepository,
    target_id: str,
    user_id: str,
    required: Permission,
) -> None:
    node = await node_repo.get_by_id(target_id)
    if not node:
        raise DiscussionPermissionError("Target not found")
    if node.owner_id == user_id:
        return
    allowed = await acl_repo.check_permission(target_id, user_id, required)
    if not allowed:
        raise DiscussionPermissionError("Permission denied")
