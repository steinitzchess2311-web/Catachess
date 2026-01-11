"""
Permission policy rules.

Defines who can do what on which objects.
"""

from workspace.domain.models.acl import ACLModel
from workspace.domain.models.node import NodeModel
from workspace.domain.models.types import Permission


class PermissionPolicy:
    """
    Permission decision engine.

    Implements business rules for access control.
    """

    @staticmethod
    def can_read(node: NodeModel, user_id: str, acl: ACLModel | None) -> bool:
        """
        Check if user can read a node.

        Args:
            node: Node to check
            user_id: User ID
            acl: ACL entry (None if no explicit permission)

        Returns:
            True if user can read
        """
        # Owner can always read
        if node.owner_id == user_id:
            return True

        # Check ACL
        if acl is not None and acl.can_read():
            return True

        return False

    @staticmethod
    def can_write(node: NodeModel, user_id: str, acl: ACLModel | None) -> bool:
        """
        Check if user can write to a node.

        Args:
            node: Node to check
            user_id: User ID
            acl: ACL entry

        Returns:
            True if user can write
        """
        # Owner can always write
        if node.owner_id == user_id:
            return True

        # Check ACL
        if acl is not None and acl.can_write():
            return True

        return False

    @staticmethod
    def can_delete(node: NodeModel, user_id: str, acl: ACLModel | None) -> bool:
        """
        Check if user can delete a node.

        Args:
            node: Node to check
            user_id: User ID
            acl: ACL entry

        Returns:
            True if user can delete
        """
        # Owner can always delete
        if node.owner_id == user_id:
            return True

        # Check ACL (requires admin or owner permission)
        if acl is not None and acl.can_delete():
            return True

        return False

    @staticmethod
    def can_manage_acl(node: NodeModel, user_id: str, acl: ACLModel | None) -> bool:
        """
        Check if user can manage ACL for a node.

        Args:
            node: Node to check
            user_id: User ID
            acl: ACL entry

        Returns:
            True if user can manage ACL
        """
        # Owner can always manage ACL
        if node.owner_id == user_id:
            return True

        # Check ACL (requires admin or owner permission)
        if acl is not None and acl.can_manage_acl():
            return True

        return False

    @staticmethod
    def can_share(node: NodeModel, user_id: str, acl: ACLModel | None) -> bool:
        """
        Check if user can share a node.

        Args:
            node: Node to check
            user_id: User ID
            acl: ACL entry

        Returns:
            True if user can share
        """
        # Same as manage_acl
        return PermissionPolicy.can_manage_acl(node, user_id, acl)

    @staticmethod
    def can_move(node: NodeModel, user_id: str, acl: ACLModel | None) -> bool:
        """
        Check if user can move a node.

        Args:
            node: Node to check
            user_id: User ID
            acl: ACL entry

        Returns:
            True if user can move
        """
        # Moving requires write permission
        return PermissionPolicy.can_write(node, user_id, acl)

    @staticmethod
    def can_create_child(parent: NodeModel, user_id: str, acl: ACLModel | None) -> bool:
        """
        Check if user can create children under a node.

        Args:
            parent: Parent node
            user_id: User ID
            acl: ACL entry for parent

        Returns:
            True if user can create children
        """
        # Creating children requires write permission on parent
        return PermissionPolicy.can_write(parent, user_id, acl)

    @staticmethod
    def get_effective_permission(
        node: NodeModel, user_id: str, acl: ACLModel | None
    ) -> Permission | None:
        """
        Get effective permission level for user on node.

        Args:
            node: Node to check
            user_id: User ID
            acl: ACL entry

        Returns:
            Effective permission level or None
        """
        # Owner has owner permission
        if node.owner_id == user_id:
            return Permission.OWNER

        # Return ACL permission
        if acl is not None:
            return acl.permission

        return None


class InheritancePolicy:
    """
    Policy for ACL inheritance.

    Defines how permissions propagate through the node tree.
    """

    @staticmethod
    def should_inherit_to_children(acl: ACLModel) -> bool:
        """
        Check if ACL should be inherited to children.

        Args:
            acl: ACL entry

        Returns:
            True if should inherit
        """
        return acl.inherit_to_children and not acl.is_inherited

    @staticmethod
    def create_inherited_acl(
        parent_acl: ACLModel, child_object_id: str
    ) -> dict[str, any]:
        """
        Create inherited ACL entry data.

        Args:
            parent_acl: Parent ACL to inherit from
            child_object_id: Child object ID

        Returns:
            Dict with inherited ACL data
        """
        return {
            "object_id": child_object_id,
            "user_id": parent_acl.user_id,
            "permission": parent_acl.permission,
            "inherit_to_children": True,
            "is_inherited": True,
            "inherited_from": parent_acl.object_id,
            "granted_by": parent_acl.granted_by,
        }

    @staticmethod
    def should_propagate_changes(
        acl: ACLModel, changed_field: str
    ) -> bool:
        """
        Check if ACL changes should propagate to inherited entries.

        Args:
            acl: ACL entry that changed
            changed_field: Field that was changed

        Returns:
            True if changes should propagate
        """
        # Changes propagate if inherit_to_children is True
        # and the changed field affects inherited permissions
        if not acl.inherit_to_children:
            return False

        propagatable_fields = {"permission", "inherit_to_children"}
        return changed_field in propagatable_fields
