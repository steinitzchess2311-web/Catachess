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

_ROOT_FOLDER_TITLE = "classroom"


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
    """POST /api/v1/workspace/share/{node_id}/users. Returns True on success."""
    try:
        res = httpx.post(
            f"{_api_base()}/api/v1/workspace/share/{node_id}/users",
            json={"user_id": user_id, "permission": "editor", "inherit_to_children": False},
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
        # Ensure ACL entry exists (idempotent: share service ignores duplicates)
        try:
            token = _make_token(teacher_uuid)
            _share_folder_with_user(token, node_id=existing_root_folder_id, user_id=teacher_uuid)
        except Exception:
            pass
        return existing_root_folder_id

    try:
        token = _make_token(teacher_uuid)
        node_id = _create_folder(token, title=_ROOT_FOLDER_TITLE, parent_id=None)
        if node_id:
            log.info(f"[workspace_sync] Created root folder '{_ROOT_FOLDER_TITLE}' (node={node_id})")
            # Share with the teacher so it appears in the Shared section (not Private)
            _share_folder_with_user(token, node_id=node_id, user_id=teacher_uuid)
        return node_id
    except Exception as exc:
        log.error(f"[workspace_sync] sync_get_or_create_root_folder failed: {exc}")
        return None


def sync_get_or_create_student_folder(
    teacher_uuid: str,
    root_folder_id: str,
    student_username: str,
    existing_student_folder_id: Optional[str],
) -> Optional[str]:
    """
    Create '{student_username}/' under classroom/ in the teacher's workspace.

    This folder belongs to the TEACHER. The student does not get automatic
    access — content enters here only when the student explicitly shares
    within the classroom (future feature).

    If `existing_student_folder_id` is provided (student already in another
    classroom of the same teacher), reuse it instead of creating a duplicate.

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
        if node_id:
            log.info(
                f"[workspace_sync] Created student folder '{student_username}' "
                f"(node={node_id}) under classroom/ {root_folder_id}"
            )
        return node_id
    except Exception as exc:
        log.error(
            f"[workspace_sync] sync_get_or_create_student_folder failed "
            f"(student={student_username}): {exc}"
        )
        return None


def _move_node(token: str, node_id: str, new_parent_id: str) -> bool:
    """POST /api/v1/workspace/nodes/{node_id}/move. Returns True on success."""
    try:
        res = httpx.post(
            f"{_api_base()}/api/v1/workspace/nodes/{node_id}/move",
            json={"new_parent_id": new_parent_id},
            headers={"Authorization": f"Bearer {token}"},
            timeout=5.0,
        )
        if res.status_code in (200, 204):
            return True
        log.warning(
            f"[workspace_sync] _move_node node={node_id} parent={new_parent_id} "
            f"→ {res.status_code}: {res.text[:200]}"
        )
        return False
    except Exception as exc:
        log.error(f"[workspace_sync] _move_node node={node_id} failed: {exc}")
        return False


def sync_share_node_with_teacher(
    student_uuid: str,
    node_id: str,
    teacher_uuid: str,
    student_folder_id: Optional[str] = None,
) -> bool:
    """
    Share a student's workspace node with their teacher and place it inside
    the student's subfolder in the teacher's classroom/ workspace.

    Full flow when student_folder_id is provided:
      1. Move the node into classroom/{student_username}/ (changes parent_id).
         The node leaves the student's private root — this is expected.
      2. Grant teacher 'viewer' ACL with inherit_to_children=True so the
         teacher can read the node and all its children (study chapters).
      3. Grant student 'editor' ACL on classroom/{student_username}/ so the
         student can still access and edit their shared nodes via their
         Shared section. (Idempotent — safe to call on every share.)

    Result for teacher: Shared → classroom/ → {username}/ → shared node  ✓
    Result for student: Shared → {username}/ → shared node  (edit access) ✓

    When student_folder_id is None (folder not yet provisioned), falls back
    to a pure ACL share — node appears in teacher's Shared root.

    Returns True on success, False on failure. Never raises.
    """
    try:
        student_token = _make_token(student_uuid)

        if student_folder_id:
            # Step 1: move node into classroom/{username}/
            moved = _move_node(student_token, node_id=node_id, new_parent_id=student_folder_id)
            if not moved:
                log.warning(
                    f"[workspace_sync] Could not move node {node_id} to "
                    f"folder {student_folder_id}; falling back to ACL-only share"
                )

            # Step 2: give teacher viewer ACL on the node
            _share_folder_with_user(student_token, node_id=node_id, user_id=teacher_uuid)

            # Step 3: give student editor ACL on their own subfolder
            # (teacher's token — teacher owns the folder)
            teacher_token = _make_token(teacher_uuid)
            res = httpx.post(
                f"{_api_base()}/api/v1/workspace/share/{student_folder_id}/users",
                json={
                    "user_id": student_uuid,
                    "permission": "editor",
                    "inherit_to_children": True,
                },
                headers={"Authorization": f"Bearer {teacher_token}"},
                timeout=5.0,
            )
            if res.status_code not in (200, 201):
                log.warning(
                    f"[workspace_sync] Could not grant student editor ACL on folder "
                    f"{student_folder_id}: {res.status_code} {res.text[:200]}"
                )

            log.info(
                f"[workspace_sync] Student {student_uuid} shared node {node_id} "
                f"→ folder {student_folder_id} (teacher={teacher_uuid})"
            )
            return True

        # Fallback: pure ACL share (no folder provisioned yet)
        res = httpx.post(
            f"{_api_base()}/api/v1/workspace/share/{node_id}/users",
            json={
                "user_id": teacher_uuid,
                "permission": "viewer",
                "inherit_to_children": True,
            },
            headers={"Authorization": f"Bearer {student_token}"},
            timeout=5.0,
        )
        if res.status_code in (200, 201):
            log.info(
                f"[workspace_sync] Student {student_uuid} shared node {node_id} "
                f"with teacher {teacher_uuid} (ACL-only fallback)"
            )
            return True
        log.warning(
            f"[workspace_sync] sync_share_node_with_teacher fallback node={node_id} "
            f"→ {res.status_code}: {res.text[:200]}"
        )
        return False
    except Exception as exc:
        log.error(
            f"[workspace_sync] sync_share_node_with_teacher node={node_id} failed: {exc}"
        )
        return False


# ── Fork helpers (material feature) ──────────────────────────────────────────

def _create_study(token: str, title: str, parent_folder_id: Optional[str]) -> Optional[str]:
    """POST /api/v1/workspace/studies. Returns new study_id or None."""
    payload: dict = {"title": title, "visibility": "shared"}
    if parent_folder_id:
        payload["parent_id"] = parent_folder_id
    try:
        res = httpx.post(
            f"{_api_base()}/api/v1/workspace/studies",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
            timeout=10.0,
        )
        if res.status_code in (200, 201):
            data = res.json()
            return data.get("id") or data.get("study_id")
        log.warning(f"[workspace_sync] _create_study '{title}' → {res.status_code}: {res.text[:200]}")
        return None
    except Exception as exc:
        log.error(f"[workspace_sync] _create_study '{title}' failed: {exc}")
        return None


def _create_chapter(token: str, study_id: str, title: str) -> Optional[str]:
    """POST /api/v1/workspace/studies/{study_id}/chapters. Returns chapter_id or None."""
    try:
        res = httpx.post(
            f"{_api_base()}/api/v1/workspace/studies/{study_id}/chapters",
            json={"title": title},
            headers={"Authorization": f"Bearer {token}"},
            timeout=10.0,
        )
        if res.status_code in (200, 201):
            data = res.json()
            return data.get("id") or data.get("chapter_id")
        log.warning(f"[workspace_sync] _create_chapter '{title}' → {res.status_code}: {res.text[:200]}")
        return None
    except Exception as exc:
        log.error(f"[workspace_sync] _create_chapter '{title}' failed: {exc}")
        return None


def _get_tree(token: str, chapter_id: str) -> Optional[dict]:
    """GET /api/v1/workspace/studies/study-patch/chapter/{chapter_id}/tree. Returns raw tree JSON or None."""
    try:
        res = httpx.get(
            f"{_api_base()}/api/v1/workspace/studies/study-patch/chapter/{chapter_id}/tree",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10.0,
        )
        if res.status_code == 200:
            data = res.json()
            return data.get("tree") if "tree" in data else data
        log.warning(f"[workspace_sync] _get_tree chapter={chapter_id} → {res.status_code}: {res.text[:200]}")
        return None
    except Exception as exc:
        log.error(f"[workspace_sync] _get_tree chapter={chapter_id} failed: {exc}")
        return None


def _put_tree(token: str, chapter_id: str, tree_data: dict) -> bool:
    """PUT /api/v1/workspace/studies/study-patch/chapter/{chapter_id}/tree. Returns True on success."""
    try:
        res = httpx.put(
            f"{_api_base()}/api/v1/workspace/studies/study-patch/chapter/{chapter_id}/tree",
            json=tree_data,
            headers={"Authorization": f"Bearer {token}"},
            timeout=10.0,
        )
        if res.status_code in (200, 204):
            return True
        log.warning(f"[workspace_sync] _put_tree chapter={chapter_id} → {res.status_code}: {res.text[:200]}")
        return False
    except Exception as exc:
        log.error(f"[workspace_sync] _put_tree chapter={chapter_id} failed: {exc}")
        return False


def _stamp_is_base(tree_data: dict) -> dict:
    """Deep-copy tree and stamp is_base=true on every node."""
    import copy
    tree = copy.deepcopy(tree_data)
    nodes = tree.get("nodes", {})
    for node in nodes.values():
        node["is_base"] = True
    return tree


def sync_fork_material(
    teacher_uuid: str,
    student_uuid: str,
    student_folder_id: Optional[str],
    source_study_id: str,
    source_chapter_id: str,
    assignment_title: str,
) -> Optional[tuple]:
    """
    Fork a teacher's chapter into the student's workspace folder.

    1. GET teacher's tree
    2. Stamp is_base=true on all nodes
    3. Create study in student's folder (teacher token — teacher owns the folder)
    4. Create chapter, PUT stamped tree
    5. Share study with student as editor
    6. Return (fork_study_id, fork_chapter_id) or None on failure
    """
    try:
        teacher_token = _make_token(teacher_uuid)

        # 1. Get source tree
        raw_tree = _get_tree(teacher_token, source_chapter_id)
        if not raw_tree:
            log.error(f"[workspace_sync] sync_fork_material: could not get source tree chapter={source_chapter_id}")
            return None

        # 2. Stamp is_base
        stamped_tree = _stamp_is_base(raw_tree)

        # 3. Create study in student's folder (teacher owns it)
        study_title = f"[Material] {assignment_title}"[:200]
        fork_study_id = _create_study(teacher_token, study_title, student_folder_id)
        if not fork_study_id:
            log.error("[workspace_sync] sync_fork_material: could not create fork study")
            return None

        # 4. Create chapter + PUT tree
        fork_chapter_id = _create_chapter(teacher_token, fork_study_id, "Chapter 1")
        if not fork_chapter_id:
            log.error("[workspace_sync] sync_fork_material: could not create fork chapter")
            return None

        ok = _put_tree(teacher_token, fork_chapter_id, stamped_tree)
        if not ok:
            log.warning("[workspace_sync] sync_fork_material: tree upload failed but continuing")

        # 5. Share study with student as editor
        _share_folder_with_user(teacher_token, node_id=fork_study_id, user_id=student_uuid)

        log.info(
            f"[workspace_sync] Forked material: study={fork_study_id} chapter={fork_chapter_id} "
            f"student={student_uuid}"
        )
        return (fork_study_id, fork_chapter_id)

    except Exception as exc:
        log.error(f"[workspace_sync] sync_fork_material failed: {exc}")
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
