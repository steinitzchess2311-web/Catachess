from workspace.db.base import Base
from workspace.db.session import get_db_config, init_db
from workspace.db.tables.acl import ACL
from workspace.db.tables.nodes import Node
from workspace.domain.models.types import NodeType, Permission, Visibility


async def init_test_db() -> None:
    """Initialize in-memory test database and create all tables."""
    config = init_db("sqlite+aiosqlite:///:memory:", echo=False)
    async with config.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    config._schema_ready = True


async def create_study_node(session, node_id: str, owner_id: str) -> Node:
    node = Node(
        id=node_id,
        node_type=NodeType.STUDY,
        title="Study",
        description=None,
        owner_id=owner_id,
        visibility=Visibility.PRIVATE,
        parent_id=None,
        path=f"/{node_id}/",
        depth=0,
        layout={},
        version=1,
    )
    session.add(node)
    await session.flush()
    return node


async def grant_acl(
    session,
    object_id: str,
    user_id: str,
    permission: Permission,
    granted_by: str,
) -> ACL:
    acl = ACL(
        id=f"acl-{object_id}-{user_id}",
        object_id=object_id,
        user_id=user_id,
        permission=permission,
        inherit_to_children=True,
        is_inherited=False,
        inherited_from=None,
        granted_by=granted_by,
    )
    session.add(acl)
    await session.flush()
    return acl
