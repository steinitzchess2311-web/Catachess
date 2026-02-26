"""
Workspace Sync Service
======================
Manages the teacher's 'My Classroom/' folder structure in their workspace.

Target structure:
  My Classroom/               ← one root per teacher, shared across all classrooms
    {student_username}/       ← one folder per student, deduped across classrooms

Design principles:
- Fire-and-try: all failures are logged, never raised to the caller.
- Classroom DB is the source of truth; workspace folders are a convenience view.
- V1 append-only: folders are created but never deleted (prevents data loss).
- Root folder and student folders are deduped: IDs come from the caller,
  who is responsible for checking existing records before calling here.

Mechanism:
- Generates a short-lived JWT for the teacher via the shared JWT secret.
- Calls workspace API via httpx (sync).
- WORKSPACE_INTERNAL_URL env var overrides the public URL for Railway internal networking.
"""
import logging
import os
from typing import Optional

import httpx

log = logging.getLogger(__name__)

_ROOT_FOLDER_TITLE = "My Classroom"


# ── Internal helpers ──────────────────────────────────────────────────────────

def _api_base() -> str:
    return os.getenv("WORKSPACE_INTERNAL_URL", "https://api.catachess.com")


def _make_token(teacher_uuid: str) -> str:
    from core.security.jwt import create_access_token
    return create_access_token(teacher_uuid)


def _create_folder(token: str, title: str, parent_id: Optional[str]) -> Optional[str]:
    """POST /api/v1/workspace/nodes. Returns new node_id or None."""
    payload: dict = {
        "node_type": "folder",
        "title": title,
        "visibility": "shared",
    }
    if parent_id:
        payload["parent_id"] = parent_id

    try:
        res = httpx.post(
            f"{_api_base()}/api/v1/workspace/nodes",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
            timeout=5.0,
        )
        if res.status_code in (200, 201):
            return res.json().get("id")
        log.warning(
            f"[workspace_sync] _create_folder '{title}' → {res.status_code}: {res.text[:200]}"
        )
        return None
    except Exception as exc:
        log.error(f"[workspace_sync] _create_folder '{title}' failed: {exc}")
        return None


def _share_folder_with_user(token: str, node_id: str, user_id: str) -> bool:
    """
    POST /api/v1/workspace/share/{node_id}/users
    Grant editor access so the node appears in the user's 'Shared with me'.
    inherit_to_children=True so all subfolders are accessible too.
    """
    try:
        res = httpx.post(
            f"{_api_base()}/api/v1/workspace/share/{node_id}/users",
            json={
                "user_id": user_id,
                "permission": "editor",
                "inherit_to_children": True,
            },
            headers={"Authorization": f"Bearer {token}"},
            timeout=5.0,
        )
        if res.status_code in (200, 201):
            return True
        log.warning(
            f"[workspace_sync] _share_folder_with_user node={node_id} user={user_id} "
            f"→ {res.status_code}: {res.text[:200]}"
        )
        return False
    except Exception as exc:
        log.error(f"[workspace_sync] _share_folder_with_user node={node_id} failed: {exc}")
        return False


def _rename_folder(token: str, node_id: str, new_title: str) -> bool:
    """PUT /api/v1/workspace/nodes/{node_id}. Returns True on success."""
    try:
        res = httpx.put(
            f"{_api_base()}/api/v1/workspace/nodes/{node_id}",
            json={"title": new_title},
            headers={"Authorization": f"Bearer {token}"},
            timeout=5.0,
        )
        if res.status_code in (200, 204):
            return True
        log.warning(
            f"[workspace_sync] _rename_folder node={node_id} → {res.status_code}: {res.text[:200]}"
        )
        return False
    except Exception as exc:
        log.error(f"[workspace_sync] _rename_folder node={node_id} failed: {exc}")
        return False


# ── Public API ────────────────────────────────────────────────────────────────

def sync_get_or_create_root_folder(
    teacher_uuid: str,
    existing_root_folder_id: Optional[str],
) -> Optional[str]:
    """
    Return the 'My Classroom/' root folder ID for this teacher.

    If `existing_root_folder_id` is provided (found on another classroom of the
    same teacher), it is returned immediately without any API call.
    Otherwise, create a new 'My Classroom/' folder and return its ID.

    Called during classroom creation.
    """
    if existing_root_folder_id:
        log.info(f"[workspace_sync] Reusing existing root folder {existing_root_folder_id}")
        return existing_root_folder_id

    try:
        token = _make_token(teacher_uuid)
        node_id = _create_folder(token, title=_ROOT_FOLDER_TITLE, parent_id=None)
        if node_id:
            log.info(f"[workspace_sync] Created root folder '{_ROOT_FOLDER_TITLE}' (node={node_id})")
        return node_id
    except Exception as exc:
        log.error(f"[workspace_sync] sync_get_or_create_root_folder failed: {exc}")
        return None


def sync_get_or_create_student_folder(
    teacher_uuid: str,
    root_folder_id: str,
    student_username: str,
    student_uuid: str,
    existing_student_folder_id: Optional[str],
) -> Optional[str]:
    """
    Return the student subfolder ID under 'My Classroom/'.

    If `existing_student_folder_id` is provided (found on another classroom of
    the same teacher for the same student), it is returned immediately without
    creating a new folder or re-sharing (share already exists).

    Otherwise:
    1. Create '{student_username}/' under root_folder_id.
    2. Share it with the student (editor + inherit_to_children) so it appears
       in their 'Shared with me' section.

    Called when a student joins or is added to a classroom.
    """
    if existing_student_folder_id:
        log.info(
            f"[workspace_sync] Reusing existing student folder "
            f"{existing_student_folder_id} for '{student_username}'"
        )
        return existing_student_folder_id

    try:
        token = _make_token(teacher_uuid)
        node_id = _create_folder(token, title=student_username, parent_id=root_folder_id)
        if not node_id:
            return None

        log.info(
            f"[workspace_sync] Created student folder '{student_username}' "
            f"(node={node_id}) under root {root_folder_id}"
        )

        # Share the folder with the student so it appears in their 'Shared with me'
        shared = _share_folder_with_user(token, node_id=node_id, user_id=student_uuid)
        if shared:
            log.info(
                f"[workspace_sync] Shared folder {node_id} with student {student_username}"
            )

        return node_id
    except Exception as exc:
        log.error(
            f"[workspace_sync] sync_get_or_create_student_folder failed "
            f"(student={student_username}): {exc}"
        )
        return None


def sync_rename_student_folder(
    teacher_uuid: str,
    folder_node_id: str,
    new_title: str,
) -> bool:
    """
    Rename a student's workspace folder (e.g. username → real name).
    Returns True on success, False on failure. Never raises.

    Called from PATCH /classrooms/{id}/members/{username}/folder.
    """
    try:
        token = _make_token(teacher_uuid)
        ok = _rename_folder(token, node_id=folder_node_id, new_title=new_title)
        if ok:
            log.info(f"[workspace_sync] Renamed folder {folder_node_id} → '{new_title}'")
        return ok
    except Exception as exc:
        log.error(f"[workspace_sync] sync_rename_student_folder failed: {exc}")
        return False
