from modules.workspace.domain.models.acl import ACLModel
from modules.workspace.domain.models.node import NodeModel
from modules.workspace.domain.models.types import Permission


class PermissionPolicy:
    @staticmethod
    def can_read(node: NodeModel, user_id: str, acl: ACLModel | None) -> bool:
        if node.owner_id == user_id:
            return True
        vis = getattr(node.visibility, 'value', node.visibility)
        if vis == 'public':
            return True
        if acl is not None and acl.can_read():
            return True
        return False

    @staticmethod
    def can_write(node: NodeModel, user_id: str, acl: ACLModel | None) -> bool:
        if node.owner_id == user_id:
            return True
        if acl is not None and acl.can_write():
            return True
        return False

    @staticmethod
    def can_delete(node: NodeModel, user_id: str, acl: ACLModel | None) -> bool:
        if node.owner_id == user_id:
            return True
        if acl is not None and acl.can_delete():
            return True
        return False

    @staticmethod
    def can_manage_acl(node: NodeModel, user_id: str, acl: ACLModel | None) -> bool:
        if node.owner_id == user_id:
            return True
        if acl is not None and acl.can_manage_acl():
            return True
        return False

    @staticmethod
    def can_share(node: NodeModel, user_id: str, acl: ACLModel | None) -> bool:
        return PermissionPolicy.can_manage_acl(node, user_id, acl)

    @staticmethod
    def can_move(node: NodeModel, user_id: str, acl: ACLModel | None) -> bool:
        return PermissionPolicy.can_write(node, user_id, acl)

    @staticmethod
    def can_create_child(parent: NodeModel, user_id: str, acl: ACLModel | None) -> bool:
        return PermissionPolicy.can_write(parent, user_id, acl)

    @staticmethod
    def get_effective_permission(
        node: NodeModel, user_id: str, acl: ACLModel | None
    ) -> Permission | None:
        if node.owner_id == user_id:
            return Permission.OWNER
        if acl is not None:
            return acl.permission
        return None
