"""
Node endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from modules.workspace.api.deps import get_current_user_id, get_node_service
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

router = APIRouter(prefix="/nodes", tags=["nodes"])


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
