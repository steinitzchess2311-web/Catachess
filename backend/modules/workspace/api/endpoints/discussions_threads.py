from fastapi import APIRouter, Depends, HTTPException, status

from workspace.api.audit_helpers import log_permission_denial
from workspace.api.deps import (
    get_acl_repo,
    get_audit_repo,
    get_current_user_id,
    get_node_repo,
    get_rate_limiter,
    get_thread_repo,
    get_thread_service,
)
from workspace.api.rate_limit import RateLimiter
from workspace.api.schemas.discussion_thread import ThreadCreate, ThreadResponse, ThreadUpdate
from workspace.db.repos.acl_repo import ACLRepository
from workspace.db.repos.discussion_thread_repo import DiscussionThreadRepository
from workspace.db.repos.node_repo import NodeRepository
from workspace.domain.models.discussion_thread import CreateThreadCommand, UpdateThreadCommand
from workspace.domain.policies.discussion_permissions import (
    DiscussionPermissionError,
    require_admin_access,
    require_commenter_access,
    require_editor_access,
    require_viewer_access,
)
from workspace.domain.policies.limits import DiscussionLimits
from workspace.domain.services.discussion.thread_service import (
    OptimisticLockError,
    ThreadNotFoundError,
    ThreadService,
)
router = APIRouter(prefix="/discussions", tags=["discussions"])
@router.post("", response_model=ThreadResponse, status_code=status.HTTP_201_CREATED)
async def create_thread(
    data: ThreadCreate, user_id: str = Depends(get_current_user_id),
    service: ThreadService = Depends(get_thread_service),
    node_repo: NodeRepository = Depends(get_node_repo), acl_repo: ACLRepository = Depends(get_acl_repo),
    audit_repo = Depends(get_audit_repo),
    rate_limiter: RateLimiter = Depends(get_rate_limiter),
) -> ThreadResponse:
    try:
        await require_commenter_access(node_repo, acl_repo, data.target_id, user_id)
        if not rate_limiter.allow(
            f"discussion:thread:{user_id}",
            DiscussionLimits.MAX_THREADS_PER_MINUTE,
            60,
        ):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
            )
        command = CreateThreadCommand(
            target_id=data.target_id,
            target_type=data.target_type,
            author_id=user_id,
            title=data.title,
            content=data.content,
            thread_type=data.thread_type,
        )
        thread = await service.create_thread(command)
        return ThreadResponse.model_validate(thread)
    except DiscussionPermissionError as exc:
        await log_permission_denial(audit_repo, user_id, data.target_id, data.target_type, "commenter", str(exc))
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

@router.get("", response_model=list[ThreadResponse])
async def list_threads(
    target_id: str,
    target_type: str,
    user_id: str = Depends(get_current_user_id),
    node_repo: NodeRepository = Depends(get_node_repo),
    acl_repo: ACLRepository = Depends(get_acl_repo),
    repo: DiscussionThreadRepository = Depends(get_thread_repo),
) -> list[ThreadResponse]:
    try:
        await require_viewer_access(node_repo, acl_repo, target_id, user_id)
        threads = await repo.list_by_target(target_id, target_type)
        return [ThreadResponse.model_validate(thread) for thread in threads]
    except DiscussionPermissionError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

@router.put("/{thread_id}", response_model=ThreadResponse)
async def update_thread(
    thread_id: str,
    data: ThreadUpdate, user_id: str = Depends(get_current_user_id),
    service: ThreadService = Depends(get_thread_service), repo: DiscussionThreadRepository = Depends(get_thread_repo),
    node_repo: NodeRepository = Depends(get_node_repo), acl_repo: ACLRepository = Depends(get_acl_repo),
    audit_repo = Depends(get_audit_repo),
) -> ThreadResponse:
    try:
        thread = await repo.get_by_id(thread_id)
        if not thread:
            raise ThreadNotFoundError(f"Thread {thread_id} not found")
        if thread.author_id != user_id:
            await require_editor_access(node_repo, acl_repo, thread.target_id, user_id)
        command = UpdateThreadCommand(
            thread_id=thread_id,
            title=data.title,
            content=data.content,
            actor_id=user_id,
            version=data.version,
        )
        thread = await service.update_thread(command)
        return ThreadResponse.model_validate(thread)
    except ThreadNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except DiscussionPermissionError as exc:
        await log_permission_denial(audit_repo, user_id, thread.target_id, thread.target_type, "editor", str(exc))
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except OptimisticLockError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

@router.delete("/{thread_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_thread(
    thread_id: str,
    service: ThreadService = Depends(get_thread_service), repo: DiscussionThreadRepository = Depends(get_thread_repo),
    user_id: str = Depends(get_current_user_id),
    node_repo: NodeRepository = Depends(get_node_repo), acl_repo: ACLRepository = Depends(get_acl_repo),
    audit_repo = Depends(get_audit_repo),
) -> None:
    try:
        thread = await repo.get_by_id(thread_id)
        if not thread:
            raise ThreadNotFoundError(f"Thread {thread_id} not found")
        if thread.author_id != user_id:
            await require_admin_access(node_repo, acl_repo, thread.target_id, user_id)
        await service.delete_thread(thread_id)
    except ThreadNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except DiscussionPermissionError as exc:
        await log_permission_denial(audit_repo, user_id, thread.target_id, thread.target_type, "admin", str(exc))
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
