"""
Created at: 2026-07-09 02:09 EDT
Created by: Codex
Last Modified at: 2026-07-09 02:35 EDT
Last Modified by: Codex

Tests for workspace share invitations creating bell notifications.
"""

import pytest
from sqlalchemy.exc import IntegrityError

from modules.workspace.db.repos.notification_repo import NotificationRepository
from modules.workspace.db.tables.users import User
from modules.workspace.domain.models.acl import ShareCommand
from modules.workspace.domain.models.node import CreateNodeCommand
from modules.workspace.domain.models.types import NodeType, Permission, Visibility


OWNER_ID = "11111111-1111-4111-8111-111111111111"
STUDENT_ID = "22222222-2222-4222-8222-222222222222"


@pytest.mark.asyncio
async def test_share_study_creates_invitation_notification(session, node_service, share_service):
    session.add(User(id=OWNER_ID, username="coach"))
    session.add(User(id=STUDENT_ID, username="student"))
    node = await node_service.create_node(
        CreateNodeCommand(
            node_type=NodeType.STUDY,
            title="Endgame Study",
            owner_id=OWNER_ID,
            visibility=Visibility.PRIVATE,
        ),
        actor_id=OWNER_ID,
    )

    await share_service.share_with_user(
        ShareCommand(
            object_id=node.id,
            user_id=STUDENT_ID,
            permission=Permission.VIEWER,
            granted_by=OWNER_ID,
        ),
        actor_id=OWNER_ID,
    )
    await session.commit()

    items = await NotificationRepository(session).list_by_user(STUDENT_ID)
    assert len(items) == 1
    notification = items[0]
    assert notification.event_type == "acl.shared"
    assert notification.payload["actor_name"] == "coach"
    assert notification.payload["target_id"] == node.id
    assert notification.payload["target_type"] == "study"
    assert notification.payload["link"] == f"/patch/workspace/{node.id}"
    assert "invited you" in notification.payload["body"]


@pytest.mark.asyncio
async def test_repeat_share_refreshes_single_notification(session, node_service, share_service):
    session.add(User(id=OWNER_ID, username="coach"))
    session.add(User(id=STUDENT_ID, username="student"))
    node = await node_service.create_node(
        CreateNodeCommand(
            node_type=NodeType.STUDY,
            title="Opening Study",
            owner_id=OWNER_ID,
            visibility=Visibility.PRIVATE,
        ),
        actor_id=OWNER_ID,
    )

    for permission in (Permission.VIEWER, Permission.EDITOR):
        await share_service.share_with_user(
            ShareCommand(
                object_id=node.id,
                user_id=STUDENT_ID,
                permission=permission,
                granted_by=OWNER_ID,
            ),
            actor_id=OWNER_ID,
        )
    await session.commit()

    items = await NotificationRepository(session).list_by_user(STUDENT_ID)
    assert len(items) == 1
    assert items[0].payload["permission"] == "editor"


@pytest.mark.asyncio
async def test_share_succeeds_when_notification_conflicts(monkeypatch, session, node_service, share_service):
    session.add(User(id=OWNER_ID, username="coach"))
    session.add(User(id=STUDENT_ID, username="student"))
    node = await node_service.create_node(
        CreateNodeCommand(
            node_type=NodeType.STUDY,
            title="Conflict Study",
            owner_id=OWNER_ID,
            visibility=Visibility.PRIVATE,
        ),
        actor_id=OWNER_ID,
    )

    async def fail_notification(**_kwargs):
        raise IntegrityError("insert", {}, Exception("duplicate notification"))

    monkeypatch.setattr(share_service, "_create_share_notification", fail_notification)

    acl = await share_service.share_with_user(
        ShareCommand(
            object_id=node.id,
            user_id=STUDENT_ID,
            permission=Permission.VIEWER,
            granted_by=OWNER_ID,
        ),
        actor_id=OWNER_ID,
    )
    await session.commit()

    assert acl.user_id == STUDENT_ID
    assert acl.permission == Permission.VIEWER
