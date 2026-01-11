"""
Share endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from workspace.api.deps import get_current_user_id, get_share_service
from workspace.api.schemas.share import (
    ACLResponse,
    ChangeRole,
    CreateShareLink,
    RevokeShare,
    ShareLinkResponse,
    ShareWithUser,
)
from workspace.domain.models.acl import (
    ChangeRoleCommand,
    CreateShareLinkCommand,
    RevokeShareCommand,
    RevokeShareLinkCommand,
    ShareCommand,
)
from workspace.domain.services.node_service import (
    NodeNotFoundError,
    NodeServiceError,
    PermissionDeniedError,
)
from workspace.domain.services.share_service import ShareService

router = APIRouter(prefix="/share", tags=["share"])


@router.post("/{object_id}/users", response_model=ACLResponse)
async def share_with_user(
    object_id: str,
    data: ShareWithUser,
    user_id: str = Depends(get_current_user_id),
    share_service: ShareService = Depends(get_share_service),
) -> ACLResponse:
    """Share a node with another user."""
    try:
        command = ShareCommand(
            object_id=object_id,
            user_id=data.user_id,
            permission=data.permission,
            granted_by=user_id,
            inherit_to_children=data.inherit_to_children,
        )

        acl = await share_service.share_with_user(command, actor_id=user_id)
        return ACLResponse.model_validate(acl)

    except NodeNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.delete("/{object_id}/users", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_share(
    object_id: str,
    data: RevokeShare,
    user_id: str = Depends(get_current_user_id),
    share_service: ShareService = Depends(get_share_service),
) -> None:
    """Revoke a user's access to a node."""
    try:
        command = RevokeShareCommand(
            object_id=object_id,
            user_id=data.user_id,
        )

        await share_service.revoke_share(command, actor_id=user_id)

    except NodeNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.put("/{object_id}/users/role", response_model=ACLResponse)
async def change_user_role(
    object_id: str,
    data: ChangeRole,
    user_id: str = Depends(get_current_user_id),
    share_service: ShareService = Depends(get_share_service),
) -> ACLResponse:
    """Change a user's permission level."""
    try:
        command = ChangeRoleCommand(
            object_id=object_id,
            user_id=data.user_id,
            new_permission=data.new_permission,
        )

        acl = await share_service.change_role(command, actor_id=user_id)
        return ACLResponse.model_validate(acl)

    except NodeNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except NodeServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{object_id}/links", response_model=ShareLinkResponse)
async def create_share_link(
    object_id: str,
    data: CreateShareLink,
    user_id: str = Depends(get_current_user_id),
    share_service: ShareService = Depends(get_share_service),
) -> ShareLinkResponse:
    """Create a shareable link."""
    try:
        command = CreateShareLinkCommand(
            object_id=object_id,
            permission=data.permission,
            created_by=user_id,
            password=data.password,
            expires_at=data.expires_at,
        )

        link = await share_service.create_share_link(command, actor_id=user_id)
        return ShareLinkResponse.model_validate(link)

    except NodeNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.delete("/links/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_share_link(
    link_id: str,
    user_id: str = Depends(get_current_user_id),
    share_service: ShareService = Depends(get_share_service),
) -> None:
    """Revoke a share link."""
    try:
        command = RevokeShareLinkCommand(link_id=link_id)
        await share_service.revoke_share_link(command, actor_id=user_id)

    except NodeServiceError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get("/shared-with-me", response_model=list)
async def get_shared_with_me(
    user_id: str = Depends(get_current_user_id),
    share_service: ShareService = Depends(get_share_service),
) -> list:
    """Get all nodes shared with the current user."""
    from workspace.api.schemas.node import NodeResponse

    shared = await share_service.get_shared_with_user(user_id)

    return [
        {
            "acl": ACLResponse.model_validate(acl),
            "node": NodeResponse.model_validate(node),
        }
        for acl, node in shared
    ]
