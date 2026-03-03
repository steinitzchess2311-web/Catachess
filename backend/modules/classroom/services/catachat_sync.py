"""
Catachat Sync Service
=====================
Keeps catachat groups in sync with classroom membership changes.

Design principles:
- All operations are fire-and-try: failure is logged, never raised.
  Classroom data is the source of truth; catachat is the messaging layer.
- Direct DB access (same process) — no HTTP round-trip.
- Role mapping: teacher → 'admin', student → 'member', owner → 'owner'

Caller is responsible for providing the catchat_group_id when known.
If catchat_group_id is None the operation is silently skipped.
"""
import logging
import uuid
from typing import Optional

log = logging.getLogger(__name__)

# Classroom role → catachat role
_ROLE_MAP = {
    "owner":   "owner",
    "teacher": "admin",
    "student": "member",
}


def _catchat_db():
    """Return a fresh catchat DB session (not a generator — caller must close)."""
    from modules.catchat.db.session import Base  # noqa: F401 — ensure models registered
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    import os

    url = os.getenv("CATCHAT_DATABASE")
    if not url:
        raise RuntimeError("CATCHAT_DATABASE not configured")
    engine = create_engine(url, pool_pre_ping=True)
    return Session(engine)


# ── Public API ────────────────────────────────────────────────────────────────

def sync_create_group(
    classroom_id: uuid.UUID,
    name: str,
    owner_user_id: str,
    owner_username: str,
) -> Optional[uuid.UUID]:
    """
    Create a catachat group for a new classroom.
    Returns the new catchat_group_id, or None on failure.
    """
    try:
        from modules.catchat.db.models.group import Group
        from modules.catchat.db.models.group_member import GroupMember

        db = _catchat_db()
        try:
            group = Group(
                name=name,
                created_by=uuid.UUID(owner_user_id),
                meta={"source": "class_group", "classroom_id": str(classroom_id)},
            )
            db.add(group)
            db.flush()

            db.add(GroupMember(
                group_id=group.id,
                user_id=uuid.UUID(owner_user_id),
                username=owner_username,
                role="owner",
            ))
            db.commit()
            log.info(f"[catachat_sync] Created group {group.id} for classroom {classroom_id}")
            return group.id
        finally:
            db.close()
    except Exception as exc:
        log.error(f"[catachat_sync] sync_create_group failed for classroom {classroom_id}: {exc}")
        return None


def sync_add_member(
    catchat_group_id: Optional[uuid.UUID],
    user_id: str,
    username: str,
    classroom_role: str,
) -> None:
    """Add a member to the catachat group."""
    if not catchat_group_id:
        return
    try:
        from modules.catchat.db.models.group_member import GroupMember
        from sqlalchemy import select

        db = _catchat_db()
        try:
            uid = uuid.UUID(user_id)
            existing = db.execute(
                select(GroupMember).where(
                    GroupMember.group_id == catchat_group_id,
                    GroupMember.user_id == uid,
                )
            ).scalar_one_or_none()
            if existing:
                return  # already a member

            db.add(GroupMember(
                group_id=catchat_group_id,
                user_id=uid,
                username=username,
                role=_ROLE_MAP.get(classroom_role, "member"),
            ))
            db.commit()
            log.info(f"[catachat_sync] Added {username} to group {catchat_group_id}")
        finally:
            db.close()
    except Exception as exc:
        log.error(f"[catachat_sync] sync_add_member failed ({username}): {exc}")


def sync_remove_member(
    catchat_group_id: Optional[uuid.UUID],
    user_id: str,
) -> None:
    """Remove a member from the catachat group."""
    if not catchat_group_id:
        return
    try:
        from modules.catchat.db.models.group_member import GroupMember
        from sqlalchemy import select

        db = _catchat_db()
        try:
            uid = uuid.UUID(user_id)
            member = db.execute(
                select(GroupMember).where(
                    GroupMember.group_id == catchat_group_id,
                    GroupMember.user_id == uid,
                )
            ).scalar_one_or_none()
            if member and member.role != "owner":
                db.delete(member)
                db.commit()
                log.info(f"[catachat_sync] Removed user {user_id} from group {catchat_group_id}")
        finally:
            db.close()
    except Exception as exc:
        log.error(f"[catachat_sync] sync_remove_member failed (user {user_id}): {exc}")


def sync_update_role(
    catchat_group_id: Optional[uuid.UUID],
    user_id: str,
    classroom_role: str,
) -> None:
    """Update a member's role in the catachat group."""
    if not catchat_group_id:
        return
    try:
        from modules.catchat.db.models.group_member import GroupMember
        from sqlalchemy import select

        db = _catchat_db()
        try:
            uid = uuid.UUID(user_id)
            member = db.execute(
                select(GroupMember).where(
                    GroupMember.group_id == catchat_group_id,
                    GroupMember.user_id == uid,
                )
            ).scalar_one_or_none()
            if member and member.role != "owner":
                member.role = _ROLE_MAP.get(classroom_role, "member")
                db.commit()
                log.info(f"[catachat_sync] Updated role for user {user_id} in group {catchat_group_id}")
        finally:
            db.close()
    except Exception as exc:
        log.error(f"[catachat_sync] sync_update_role failed (user {user_id}): {exc}")


def sync_rename_group(
    catchat_group_id: Optional[uuid.UUID],
    new_name: str,
) -> None:
    """Rename the catachat group."""
    if not catchat_group_id:
        return
    try:
        from modules.catchat.db.models.group import Group

        db = _catchat_db()
        try:
            group = db.get(Group, catchat_group_id)
            if group:
                group.name = new_name
                db.commit()
                log.info(f"[catachat_sync] Renamed group {catchat_group_id} to '{new_name}'")
        finally:
            db.close()
    except Exception as exc:
        log.error(f"[catachat_sync] sync_rename_group failed ({catchat_group_id}): {exc}")


def sync_dissolve_group(
    catchat_group_id: Optional[uuid.UUID],
) -> None:
    """Delete the catachat group (cascade removes members and messages)."""
    if not catchat_group_id:
        return
    try:
        from modules.catchat.db.models.group import Group

        db = _catchat_db()
        try:
            group = db.get(Group, catchat_group_id)
            if group:
                db.delete(group)
                db.commit()
                log.info(f"[catachat_sync] Dissolved group {catchat_group_id}")
        finally:
            db.close()
    except Exception as exc:
        log.error(f"[catachat_sync] sync_dissolve_group failed ({catchat_group_id}): {exc}")
