"""
Workspace Sync Service
======================
Creates shared folder structure in the teacher's workspace when classroom
events occur.

Target structure in teacher's workspace:
  {class_name}/              ← visibility=shared  (classroom.workspace_folder_id)
    {student_username}/      ← visibility=shared  (classroom_members.workspace_folder_id)

Design principles (same as catachat_sync):
- Fire-and-try: failure is logged, never raised to the caller.
- Classroom DB is the source of truth; workspace folders are a convenience view.
- V1 is append-only: folders are created but never renamed or deleted here
  to avoid accidental data loss.

Mechanism:
- Generates a short-lived JWT for the teacher using the shared JWT secret.
- Calls workspace API via httpx (sync) — same process, public endpoint.
- `WORKSPACE_INTERNAL_URL` env var overrides the default public URL
  (useful for internal Railway networking to avoid public round-trips).
"""
import logging
import os
from typing import Optional

import httpx

log = logging.getLogger(__name__)


def _api_base() -> str:
    return os.getenv("WORKSPACE_INTERNAL_URL", "https://api.catachess.com")


def _make_token(teacher_uuid: str) -> str:
    from core.security.jwt import create_access_token
    return create_access_token(teacher_uuid)


def _create_folder(
    token: str,
    title: str,
    parent_id: Optional[str],
) -> Optional[str]:
    """
    POST /api/v1/workspace/nodes to create a folder.
    Returns the new node_id string, or None on failure.
    """
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
            f"[workspace_sync] _create_folder '{title}' returned {res.status_code}: {res.text[:200]}"
        )
        return None
    except Exception as exc:
        log.error(f"[workspace_sync] _create_folder '{title}' failed: {exc}")
        return None


# ── Public API ────────────────────────────────────────────────────────────────

def sync_create_classroom_folder(
    teacher_uuid: str,
    classroom_id: str,
    class_name: str,
) -> Optional[str]:
    """
    Create a shared folder named `{class_name}` at the root of the teacher's
    workspace. Returns the new node_id, or None on failure.

    Called after a classroom is successfully created.
    """
    try:
        token = _make_token(teacher_uuid)
        node_id = _create_folder(token, title=class_name, parent_id=None)
        if node_id:
            log.info(
                f"[workspace_sync] Created classroom folder '{class_name}' "
                f"(node={node_id}) for classroom {classroom_id}"
            )
        return node_id
    except Exception as exc:
        log.error(
            f"[workspace_sync] sync_create_classroom_folder failed "
            f"(classroom={classroom_id}): {exc}"
        )
        return None


def sync_create_student_folder(
    teacher_uuid: str,
    classroom_folder_id: str,
    student_username: str,
) -> Optional[str]:
    """
    Create a shared subfolder named `{student_username}` under the classroom
    folder. Returns the new node_id, or None on failure.

    Called after a student successfully joins or is added to a classroom.
    """
    try:
        token = _make_token(teacher_uuid)
        node_id = _create_folder(
            token,
            title=student_username,
            parent_id=classroom_folder_id,
        )
        if node_id:
            log.info(
                f"[workspace_sync] Created student folder '{student_username}' "
                f"(node={node_id}) under classroom folder {classroom_folder_id}"
            )
        return node_id
    except Exception as exc:
        log.error(
            f"[workspace_sync] sync_create_student_folder failed "
            f"(student={student_username}): {exc}"
        )
        return None
