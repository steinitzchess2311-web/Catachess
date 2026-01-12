"""Notification endpoints."""
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from workspace.api.deps import get_current_user_id, get_session
from workspace.api.schemas.notification import (
    NotificationBulkReadRequest,
    NotificationListResponse,
    NotificationPreferencesResponse,
    NotificationPreferencesUpdate,
    NotificationReadRequest,
    NotificationResponse,
    NotificationTypeInfo,
    NotificationTypesResponse,
)
from workspace.db.repos.notification_preference_repo import NotificationPreferenceRepository
from workspace.db.repos.notification_repo import NotificationRepository
from workspace.db.tables.notification_preferences import NotificationPreference
from workspace.db.tables.notifications import Notification
from workspace.domain.policies.notification_rules import get_all_notification_types

router = APIRouter(prefix="/notifications", tags=["notifications"])


def _to_notification_response(notification: NotificationResponse | Notification) -> NotificationResponse:
    payload = getattr(notification, "payload", {}) or {}
    return NotificationResponse(
        id=notification.id,
        user_id=notification.user_id,
        actor_id=payload.get("actor_id"),
        type=notification.event_type,
        title=payload.get("title", notification.event_type),
        body=payload.get("body", payload.get("message", "")),
        target_id=payload.get("target_id"),
        target_type=payload.get("target_type"),
        data=payload,
        read_at=notification.read_at,
        created_at=notification.created_at,
    )


def get_notification_repo(session: AsyncSession = Depends(get_session)) -> NotificationRepository:
    """Get notification repository."""
    return NotificationRepository(session)


def get_preference_repo(session: AsyncSession = Depends(get_session)) -> NotificationPreferenceRepository:
    """Get notification preference repository."""
    return NotificationPreferenceRepository(session)


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Page size"),
    unread_only: bool = Query(False, description="Show only unread notifications"),
    user_id: str = Depends(get_current_user_id),
    repo: NotificationRepository = Depends(get_notification_repo),
) -> NotificationListResponse:
    """
    Get user's notifications.

    Args:
        page: Page number (1-indexed)
        page_size: Number of notifications per page
        unread_only: Filter to only unread notifications
        user_id: Current user ID
        repo: Notification repository

    Returns:
        List of notifications with pagination info
    """
    offset = (page - 1) * page_size

    if unread_only:
        notifications = await repo.get_unread(user_id)
        unread_count = len(notifications)
        total = unread_count
        # Apply pagination
        notifications = notifications[offset : offset + page_size]
    else:
        notifications = await repo.list_by_user(user_id, limit=page_size, offset=offset)
        unread = await repo.get_unread(user_id)
        unread_count = len(unread)
        # For total, we need to count all notifications
        all_notifications = await repo.list_by_user(user_id, limit=10000, offset=0)
        total = len(all_notifications)

    return NotificationListResponse(
        notifications=[_to_notification_response(n) for n in notifications],
        total=total,
        unread_count=unread_count,
        page=page,
        page_size=page_size,
    )


@router.post("/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_notifications_read(
    data: NotificationReadRequest,
    user_id: str = Depends(get_current_user_id),
    repo: NotificationRepository = Depends(get_notification_repo),
) -> None:
    """
    Mark specific notifications as read.

    Args:
        data: Request with notification IDs
        user_id: Current user ID
        repo: Notification repository
    """
    for notification_id in data.notification_ids:
        # Verify the notification belongs to the user
        notification = await repo.get_by_id(notification_id)
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Notification {notification_id} not found",
            )
        if notification.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot mark other user's notifications",
            )

        await repo.mark_as_read(notification_id)


@router.post("/bulk-read", status_code=status.HTTP_204_NO_CONTENT)
async def bulk_mark_read(
    data: NotificationBulkReadRequest,
    user_id: str = Depends(get_current_user_id),
    repo: NotificationRepository = Depends(get_notification_repo),
) -> None:
    """
    Bulk mark notifications as read.

    Args:
        data: Request with bulk read options
        user_id: Current user ID
        repo: Notification repository
    """
    if data.mark_all:
        await repo.mark_all_as_read(user_id)
    elif data.before:
        # Mark all notifications before a certain timestamp
        # This requires additional repo method
        notifications = await repo.list_by_user(user_id, limit=10000)
        for notification in notifications:
            if notification.created_at < data.before and not notification.read_at:
                await repo.mark_as_read(notification.id)


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(
    notification_id: str,
    user_id: str = Depends(get_current_user_id),
    repo: NotificationRepository = Depends(get_notification_repo),
) -> None:
    """
    Delete a notification.

    Args:
        notification_id: Notification ID
        user_id: Current user ID
        repo: Notification repository
    """
    notification = await repo.get_by_id(notification_id)
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification {notification_id} not found",
        )

    if notification.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete other user's notifications",
        )

    await repo.delete_notification(notification_id)


@router.get("/preferences", response_model=NotificationPreferencesResponse)
async def get_preferences(
    user_id: str = Depends(get_current_user_id),
    repo: NotificationPreferenceRepository = Depends(get_preference_repo),
    session: AsyncSession = Depends(get_session),
) -> NotificationPreferencesResponse:
    """
    Get user's notification preferences.

    Args:
        user_id: Current user ID
        repo: Preference repository
        session: Database session

    Returns:
        User's notification preferences
    """
    prefs = await repo.get_by_user_id(user_id)

    if not prefs:
        # Create default preferences
        import uuid

        prefs = NotificationPreference(
            id=str(uuid.uuid4()),
            user_id=user_id,
            preferences={},
            digest_frequency="instant",
            quiet_hours={},
            muted_objects=[],
            enabled=True,
        )
        prefs = await repo.create(prefs)
        await session.commit()

    return NotificationPreferencesResponse.model_validate(prefs)


@router.get("/types", response_model=NotificationTypesResponse)
async def list_notification_types() -> NotificationTypesResponse:
    """List all available notification types."""
    types = get_all_notification_types()
    items = [
        NotificationTypeInfo(
            event_type=event_type,
            description=meta.get("description", ""),
            enabled_by_default=meta.get("enabled_by_default", False),
            channels=meta.get("channels", []),
            priority=meta.get("priority", "low"),
        )
        for event_type, meta in types.items()
    ]
    return NotificationTypesResponse(types=items)


@router.put("/preferences", response_model=NotificationPreferencesResponse)
async def update_preferences(
    data: NotificationPreferencesUpdate,
    user_id: str = Depends(get_current_user_id),
    repo: NotificationPreferenceRepository = Depends(get_preference_repo),
    session: AsyncSession = Depends(get_session),
) -> NotificationPreferencesResponse:
    """
    Update user's notification preferences.

    Args:
        data: Updated preferences
        user_id: Current user ID
        repo: Preference repository
        session: Database session

    Returns:
        Updated notification preferences
    """
    import uuid

    prefs = await repo.get_by_user_id(user_id)

    if not prefs:
        # Create new preferences
        prefs = NotificationPreference(
            id=str(uuid.uuid4()),
            user_id=user_id,
            preferences=data.preferences,
            digest_frequency=data.digest_frequency,
            quiet_hours=data.quiet_hours,
            muted_objects=data.muted_objects,
            enabled=data.enabled,
        )
        prefs = await repo.create(prefs)
    else:
        # Update existing preferences
        prefs.preferences = data.preferences
        prefs.digest_frequency = data.digest_frequency
        prefs.quiet_hours = data.quiet_hours
        prefs.muted_objects = data.muted_objects
        prefs.enabled = data.enabled
        prefs.updated_at = datetime.now(UTC)

    await session.commit()
    await session.refresh(prefs)

    return NotificationPreferencesResponse.model_validate(prefs)
