"""
Group endpoints
===============
POST   /groups                              Create a group
GET    /groups                              List groups I'm a member of
GET    /groups/{id}                         Group detail + member list
PATCH  /groups/{id}                         Rename group (admin+)
DELETE /groups/{id}                         Dissolve group (owner only)

POST   /groups/{id}/members                 Add member (admin+)
DELETE /groups/{id}/members/{user_id}       Kick member or leave group
PATCH  /groups/{id}/members/{user_id}       Change member role (owner only)

Permission hierarchy:
  owner  (3) — all actions, including dissolve and role changes
  admin  (2) — add/kick members (not admins/owner), rename
  member (1) — read + send messages, leave
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from modules.catchat.auth import get_current_user
from modules.catchat.db.session import get_db
from modules.catchat.db.models.group import Group
from modules.catchat.db.models.group_member import GroupMember
from modules.catchat.schemas.group import (
    GroupCreate, GroupUpdate, GroupResponse, GroupMemberInfo,
    MemberAdd, MemberRoleUpdate,
)
from models.user import User

router = APIRouter(prefix="/groups", tags=["catchat-groups"])

ROLE_ORDER = {"owner": 3, "admin": 2, "member": 1}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _require_min_role(membership: GroupMember, role: str) -> None:
    if ROLE_ORDER.get(membership.role, 0) < ROLE_ORDER[role]:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail=f"Requires at least '{role}' role",
        )


def _get_group_or_404(db: Session, group_id: uuid.UUID) -> Group:
    g = db.get(Group, group_id)
    if not g:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Group not found")
    return g


def _get_membership_or_403(
    db: Session, group_id: uuid.UUID, user_id: uuid.UUID
) -> GroupMember:
    m = db.execute(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == user_id,
        )
    ).scalar_one_or_none()
    if not m:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Not a member of this group")
    return m


def _load_members(db: Session, group_id: uuid.UUID) -> list[GroupMember]:
    return list(
        db.execute(
            select(GroupMember)
            .where(GroupMember.group_id == group_id)
            .order_by(GroupMember.joined_at)
        ).scalars().all()
    )


def _computed_name(
    group: Group, members: list[GroupMember], viewer_id: uuid.UUID
) -> str:
    """Return stored name, or auto-generate from other members' usernames."""
    if group.name:
        return group.name
    others = [m.username for m in members if m.user_id != viewer_id]
    if not others:
        return "Just you"
    display = ", ".join(others[:3])
    return display + ("…" if len(others) > 3 else "")


def _to_response(
    group: Group, members: list[GroupMember], viewer_id: uuid.UUID
) -> GroupResponse:
    return GroupResponse(
        id=str(group.id),
        name=_computed_name(group, members, viewer_id),
        created_by=str(group.created_by),
        created_at=group.created_at,
        last_message_at=group.last_message_at,
        members=[
            GroupMemberInfo(
                user_id=str(m.user_id),
                username=m.username,
                role=m.role,
                joined_at=m.joined_at,
            )
            for m in members
        ],
        meta=group.meta,
    )


# ── Group CRUD ────────────────────────────────────────────────────────────────

@router.post("", response_model=GroupResponse, status_code=201)
def create_group(
    body: GroupCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    group = Group(
        name=body.name.strip() if body.name and body.name.strip() else None,
        created_by=current_user.id,
    )
    db.add(group)
    db.flush()  # populate group.id before creating members

    seen_ids: set[uuid.UUID] = set()
    members_to_add = []

    # Creator is always owner
    members_to_add.append(GroupMember(
        group_id=group.id,
        user_id=current_user.id,
        username=current_user.username or str(current_user.id)[:8],
        role="owner",
    ))
    seen_ids.add(current_user.id)

    for m in body.members:
        try:
            uid = uuid.UUID(m.user_id)
        except ValueError:
            continue
        if uid in seen_ids:
            continue
        seen_ids.add(uid)
        members_to_add.append(GroupMember(
            group_id=group.id,
            user_id=uid,
            username=m.username,
            role="member",
        ))

    db.add_all(members_to_add)
    db.commit()
    db.refresh(group)
    members = _load_members(db, group.id)
    return _to_response(group, members, current_user.id)


@router.get("", response_model=list[GroupResponse])
def list_my_groups(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    memberships = db.execute(
        select(GroupMember).where(GroupMember.user_id == current_user.id)
    ).scalars().all()

    group_ids = [m.group_id for m in memberships]
    if not group_ids:
        return []

    groups = db.execute(
        select(Group)
        .where(Group.id.in_(group_ids))
        .order_by(Group.last_message_at.desc())
    ).scalars().all()

    # Batch: load all members for all groups in one query instead of N queries
    all_members = db.execute(
        select(GroupMember)
        .where(GroupMember.group_id.in_(group_ids))
        .order_by(GroupMember.joined_at)
    ).scalars().all()
    members_by_group: dict[uuid.UUID, list[GroupMember]] = {}
    for m in all_members:
        members_by_group.setdefault(m.group_id, []).append(m)

    result = []
    for g in groups:
        members = members_by_group.get(g.id, [])
        result.append(_to_response(g, members, current_user.id))
    return result


@router.get("/{group_id}", response_model=GroupResponse)
def get_group(
    group_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    group = _get_group_or_404(db, group_id)
    _get_membership_or_403(db, group_id, current_user.id)
    members = _load_members(db, group_id)
    return _to_response(group, members, current_user.id)


@router.patch("/{group_id}", response_model=GroupResponse)
def rename_group(
    group_id: uuid.UUID,
    body: GroupUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    group = _get_group_or_404(db, group_id)
    membership = _get_membership_or_403(db, group_id, current_user.id)
    _require_min_role(membership, "admin")
    group.name = body.name.strip()
    db.commit()
    db.refresh(group)
    members = _load_members(db, group_id)
    return _to_response(group, members, current_user.id)


@router.delete("/{group_id}", status_code=204)
def dissolve_group(
    group_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    group = _get_group_or_404(db, group_id)
    membership = _get_membership_or_403(db, group_id, current_user.id)
    _require_min_role(membership, "owner")
    db.delete(group)
    db.commit()


# ── Member management ─────────────────────────────────────────────────────────

@router.post("/{group_id}/members", response_model=GroupResponse, status_code=201)
def add_member(
    group_id: uuid.UUID,
    body: MemberAdd,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    group = _get_group_or_404(db, group_id)
    membership = _get_membership_or_403(db, group_id, current_user.id)
    _require_min_role(membership, "admin")

    try:
        new_uid = uuid.UUID(body.user_id)
    except ValueError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid user_id")

    existing = db.execute(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == new_uid,
        )
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="User is already a member")

    db.add(GroupMember(
        group_id=group_id,
        user_id=new_uid,
        username=body.username,
        role="member",
    ))
    db.commit()
    members = _load_members(db, group_id)
    return _to_response(group, members, current_user.id)


@router.delete("/{group_id}/members/{target_user_id}", status_code=204)
def remove_member(
    group_id: uuid.UUID,
    target_user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_group_or_404(db, group_id)
    my_membership = _get_membership_or_403(db, group_id, current_user.id)

    # Leaving the group yourself
    if target_user_id == current_user.id:
        if my_membership.role == "owner":
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Owner cannot leave. Transfer ownership or dissolve the group first.",
            )
        db.delete(my_membership)
        db.commit()
        return

    # Kicking someone else — need admin+
    _require_min_role(my_membership, "admin")

    target = db.execute(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == target_user_id,
        )
    ).scalar_one_or_none()
    if not target:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Member not found")

    # Cannot kick someone of equal or higher rank
    if ROLE_ORDER.get(target.role, 0) >= ROLE_ORDER.get(my_membership.role, 0):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="Cannot remove a member of equal or higher rank",
        )

    db.delete(target)
    db.commit()


@router.patch("/{group_id}/members/{target_user_id}")
def change_member_role(
    group_id: uuid.UUID,
    target_user_id: uuid.UUID,
    body: MemberRoleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_group_or_404(db, group_id)
    my_membership = _get_membership_or_403(db, group_id, current_user.id)
    _require_min_role(my_membership, "owner")

    if body.role not in ("admin", "member"):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Role must be 'admin' or 'member'",
        )

    target = db.execute(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == target_user_id,
        )
    ).scalar_one_or_none()
    if not target:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Member not found")
    if target.role == "owner":
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Cannot change the owner's role",
        )

    target.role = body.role
    db.commit()
    return {"ok": True}
