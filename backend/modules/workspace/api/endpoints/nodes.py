"""
Node endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete as sa_delete, select

from modules.workspace.api.deps import (
    get_current_user_id,
    get_node_service,
    get_study_repository,
)
from modules.workspace.api.schemas.node import (
    NodeCreate,
    NodeListResponse,
    NodeMove,
    NodeResponse,
    NodeUpdate,
)
from modules.workspace.domain.models.node import (
    CreateNodeCommand,
    DeleteNodeCommand,
    MoveNodeCommand,
    UpdateNodeCommand,
)
from modules.workspace.domain.services.node_service import (
    InvalidOperationError,
    NodeNotFoundError,
    NodeService,
    OptimisticLockError,
    PermissionDeniedError,
)
from modules.workspace.db.repos.study_repo import StudyRepository
from modules.workspace.domain.models.types import NodeType, Visibility
from modules.workspace.db.tables.study_versions import StudyVersionTable, VersionSnapshotTable
from modules.workspace.storage.r2_client import create_r2_client_from_env
from modules.workspace.domain.policies.permissions import PermissionPolicy

router = APIRouter(prefix="/nodes", tags=["nodes"])

async def _fetch_study_ids(node_service: NodeService, root: str) -> list[str]:
    node = await node_service.node_repo.get_by_id(root, include_deleted=True)
    if node is None:
        return []
    descendants = await node_service.node_repo.get_descendants(
        node.path, include_deleted=True
    )
    nodes = [node, *descendants]
    return list({n.id for n in nodes if n.node_type == NodeType.STUDY})

async def _fetch_snapshot_keys(node_service: NodeService, study_id: str) -> list[str]:
    result = await node_service.session.execute(
        select(VersionSnapshotTable.r2_key).join(
            StudyVersionTable,
            VersionSnapshotTable.version_id == StudyVersionTable.id,
        ).where(StudyVersionTable.study_id == study_id)
    )
    return [row[0] for row in result.all()]

async def _delete_r2_objects(
    node_service: NodeService,
    study_repo: StudyRepository,
    study_id: str,
    r2_client,
) -> None:
    chapters = await study_repo.get_chapters_for_study(study_id, order_by_order=False)
    for chapter in chapters:
        if not chapter.r2_key:
            continue
        try:
            r2_client.delete(chapter.r2_key)
        except Exception:
            pass

    snapshot_keys = await _fetch_snapshot_keys(node_service, study_id)
    for key in snapshot_keys:
        try:
            r2_client.delete(key)
        except Exception:
            pass


@router.get("", response_model=NodeListResponse)
async def list_nodes(
    parent_id: str | None = Query(None),
    user_id: str = Depends(get_current_user_id),
    node_service: NodeService = Depends(get_node_service),
) -> NodeListResponse:
    """List nodes, optionally filtered by parent_id. If parent_id is 'root', returns user's root nodes."""
    if parent_id == "root" or parent_id is None:
        nodes = await node_service.node_repo.get_root_nodes(owner_id=user_id)
    else:
        try:
            nodes = await node_service.get_children(parent_id, actor_id=user_id)
        except NodeNotFoundError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent node not found")
        except PermissionDeniedError:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")

    return NodeListResponse(
        nodes=[NodeResponse.model_validate(n) for n in nodes],
        total=len(nodes),
    )


@router.post("", response_model=NodeResponse, status_code=status.HTTP_201_CREATED)
async def create_node(
    data: NodeCreate,
    user_id: str = Depends(get_current_user_id),
    node_service: NodeService = Depends(get_node_service),
    study_repo: StudyRepository = Depends(get_study_repository),
) -> NodeResponse:
    """Create a new node."""
    try:
        command = CreateNodeCommand(
            node_type=data.node_type,
            title=data.title,
            description=data.description,
            owner_id=user_id,
            parent_id=data.parent_id,
            visibility=data.visibility,
            layout=data.layout,
        )

        node = await node_service.create_node(command, actor_id=user_id)
        if node.node_type == NodeType.STUDY:
            await study_repo.ensure_study(
                node.id,
                description=data.description,
                is_public=data.visibility == Visibility.PUBLIC,
                tags=None,
            )
        return NodeResponse.model_validate(node)

    except NodeNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")


@router.get("/{node_id}", response_model=NodeResponse)
async def get_node(
    node_id: str,
    user_id: str = Depends(get_current_user_id),
    node_service: NodeService = Depends(get_node_service),
) -> NodeResponse:
    """Get a node by ID."""
    try:
        node = await node_service.get_node(node_id, actor_id=user_id)
        return NodeResponse.model_validate(node)

    except NodeNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")


@router.put("/{node_id}", response_model=NodeResponse)
async def update_node(
    node_id: str,
    data: NodeUpdate,
    user_id: str = Depends(get_current_user_id),
    node_service: NodeService = Depends(get_node_service),
) -> NodeResponse:
    """Update a node."""
    try:
        command = UpdateNodeCommand(
            node_id=node_id,
            title=data.title,
            description=data.description,
            visibility=data.visibility,
            layout=data.layout,
            version=data.version,
        )

        node = await node_service.update_node(command, actor_id=user_id)
        return NodeResponse.model_validate(node)

    except NodeNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except OptimisticLockError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/{node_id}/move", response_model=NodeResponse)
async def move_node(
    node_id: str,
    data: NodeMove,
    user_id: str = Depends(get_current_user_id),
    node_service: NodeService = Depends(get_node_service),
) -> NodeResponse:
    """Move a node to a new parent."""
    try:
        command = MoveNodeCommand(
            node_id=node_id,
            new_parent_id=data.new_parent_id,
            version=data.version,
        )

        node = await node_service.move_node(command, actor_id=user_id)
        return NodeResponse.model_validate(node)

    except NodeNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except InvalidOperationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except OptimisticLockError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.delete("/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_node(
    node_id: str,
    version: int | None = None,
    user_id: str = Depends(get_current_user_id),
    node_service: NodeService = Depends(get_node_service),
) -> None:
    """Soft delete a node."""
    try:
        command = DeleteNodeCommand(node_id=node_id, version=version or -1)
        await node_service.delete_node(command, actor_id=user_id)

    except NodeNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except OptimisticLockError as e:
        if version is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Version is required"
            )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.delete("/{node_id}/purge", status_code=status.HTTP_204_NO_CONTENT)
async def purge_node(
    node_id: str,
    version: int | None = None,
    user_id: str = Depends(get_current_user_id),
    node_service: NodeService = Depends(get_node_service),
) -> None:
    """Hard delete a node and remove related study data from Postgres and R2."""
    node = await node_service.node_repo.get_by_id(node_id, include_deleted=True)
    if node is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")

    acl = await node_service.acl_repo.get_acl(node_id, user_id)
    if not node.owner_id == user_id:
        if acl is None or not PermissionPolicy.can_delete(
            node_service._node_to_model(node), user_id, node_service._acl_to_model(acl)
        ):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")

    if version is not None and node.version != version:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Version conflict")

    study_ids = await _fetch_study_ids(node_service, node_id)
    study_repo = StudyRepository(node_service.session)

    r2_client = None
    try:
        r2_client = create_r2_client_from_env()
    except ValueError:
        r2_client = None

    if r2_client:
        for study_id in study_ids:
            await _delete_r2_objects(node_service, study_repo, study_id, r2_client)

    if study_ids:
        await node_service.session.execute(
            sa_delete(StudyVersionTable).where(StudyVersionTable.study_id.in_(study_ids))
        )

    await node_service.session.delete(node)
    await node_service.session.commit()


@router.post("/{node_id}/restore", response_model=NodeResponse)
async def restore_node(
    node_id: str,
    user_id: str = Depends(get_current_user_id),
    node_service: NodeService = Depends(get_node_service),
) -> NodeResponse:
    """Restore a soft-deleted node."""
    try:
        node = await node_service.restore_node(node_id, actor_id=user_id)
        return NodeResponse.model_validate(node)

    except NodeNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except InvalidOperationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{node_id}/children", response_model=NodeListResponse)
async def get_children(
    node_id: str,
    user_id: str = Depends(get_current_user_id),
    node_service: NodeService = Depends(get_node_service),
) -> NodeListResponse:
    """Get children of a node."""
    try:
        children = await node_service.get_children(node_id, actor_id=user_id)
        return NodeListResponse(
            nodes=[NodeResponse.model_validate(child) for child in children],
            total=len(children),
        )

    except NodeNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
