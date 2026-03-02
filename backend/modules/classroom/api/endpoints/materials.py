"""
Material fork endpoints + file upload/download
===============================================
POST  /classrooms/{id}/assignments/{aid}/open-material    Student opens material → fork
GET   /classrooms/{id}/assignments/{aid}/forks             Teacher views all forks
POST  /classrooms/{id}/assignments/{aid}/upload-material   Upload file to R2 (teacher+)
GET   /classrooms/{id}/assignments/{aid}/download-material Stream file from R2 (any member)
"""
import json
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from modules.classroom.auth import get_current_user
from modules.classroom.db.session import get_db
from modules.classroom.db.models.classroom import Classroom
from modules.classroom.db.models.member import ClassroomMember
from modules.classroom.db.models.assignment import Assignment
from modules.classroom.db.models.material_fork import MaterialFork
from modules.classroom.services import workspace_sync
from modules.classroom.storage.client import get_classroom_storage
from modules.classroom.storage.keys import material_key
from models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(tags=["classroom-materials"])


# ── Schemas ──────────────────────────────────────────────────────────────────

class OpenMaterialResponse(BaseModel):
    fork_study_id: str
    fork_chapter_id: str
    is_new: bool


class ForkItem(BaseModel):
    student_username: str
    fork_study_id: str
    fork_chapter_id: str
    created_at: str


# ── Helpers ──────────────────────────────────────────────────────────────────

def _get_classroom_or_404(db: Session, classroom_id: uuid.UUID) -> Classroom:
    c = db.get(Classroom, classroom_id)
    if not c or c.deleted_at:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Classroom not found")
    return c


def _my_role(classroom: Classroom, username: str, db: Session) -> str:
    if classroom.owner == username:
        return "owner"
    m = db.execute(
        select(ClassroomMember).where(
            ClassroomMember.classroom_id == classroom.id,
            ClassroomMember.username == username,
            ClassroomMember.removed_at.is_(None),
        )
    ).scalar_one_or_none()
    if not m:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Not a member of this classroom")
    return m.role


def _resolve_user_uuid(username: str) -> str | None:
    """Resolve a username to UUID from the main DB."""
    from core.db.deps import get_db as get_main_db
    for main_db in get_main_db():
        user = main_db.execute(
            select(User).where(User.username == username)
        ).scalar_one_or_none()
        if user:
            return str(user.id)
        break
    return None


# ── Open Material ────────────────────────────────────────────────────────────

class OpenMaterialShareResponse(BaseModel):
    """Returned when material is a shared study (ACL-based, no fork)."""
    study_id: str
    shared: bool


@router.post(
    "/classrooms/{classroom_id}/assignments/{assignment_id}/open-material",
)
def open_material(
    classroom_id: uuid.UUID,
    assignment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Student opens a material assignment.

    Two modes based on source_ref format:
    - "{study_id}/{chapter_id}" (legacy): deep-copy fork into student workspace
    - "{study_id}" (new): share teacher's study with student via ACL (viewer)
    """
    classroom = _get_classroom_or_404(db, classroom_id)
    role = _my_role(classroom, current_user.username, db)
    if role not in ("student",):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Only students can open material")

    assignment = db.execute(
        select(Assignment).where(
            Assignment.id == assignment_id,
            Assignment.classroom_id == classroom_id,
            Assignment.deleted_at.is_(None),
        )
    ).scalar_one_or_none()
    if not assignment:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    if assignment.category != "material" or assignment.source_type != "study":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Assignment is not a study material")

    source_ref = assignment.source_ref or ""
    parts = source_ref.split("/", 1)
    source_study_id = parts[0]
    if not source_study_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid source_ref: missing study ID")

    is_legacy_fork = len(parts) == 2 and bool(parts[1])

    # ── New flow: ACL share (no fork) ────────────────────────────────────
    if not is_legacy_fork:
        teacher_uuid = _resolve_user_uuid(classroom.owner)
        if not teacher_uuid:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not resolve teacher account")

        student_uuid = str(current_user.id)

        # Share the study with the student as viewer
        from modules.classroom.services.workspace_sync import _make_token, _share_folder_with_user
        teacher_token = _make_token(teacher_uuid)
        ok = _share_folder_with_user(teacher_token, node_id=source_study_id, user_id=student_uuid)
        if not ok:
            logger.warning(
                f"open_material: ACL share failed study={source_study_id} student={student_uuid}"
            )
            # Non-fatal — student might already have access

        return OpenMaterialShareResponse(study_id=source_study_id, shared=True)

    # ── Legacy flow: deep-copy fork ──────────────────────────────────────
    source_chapter_id = parts[1]

    # Check for existing fork
    existing = db.execute(
        select(MaterialFork).where(
            MaterialFork.assignment_id == assignment_id,
            MaterialFork.student_username == current_user.username,
        )
    ).scalar_one_or_none()

    if existing:
        return OpenMaterialResponse(
            fork_study_id=existing.fork_study_id,
            fork_chapter_id=existing.fork_chapter_id,
            is_new=False,
        )

    teacher_uuid = _resolve_user_uuid(classroom.owner)
    if not teacher_uuid:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not resolve teacher account")

    student_uuid = str(current_user.id)

    # Get student's workspace folder (lazy backfill if missing)
    member = db.execute(
        select(ClassroomMember).where(
            ClassroomMember.classroom_id == classroom_id,
            ClassroomMember.username == current_user.username,
            ClassroomMember.removed_at.is_(None),
        )
    ).scalar_one_or_none()
    student_folder_id = member.workspace_folder_id if member else None

    if not student_folder_id and classroom.workspace_folder_id:
        ws_folder_id = workspace_sync.sync_get_or_create_student_folder(
            teacher_uuid=teacher_uuid,
            root_folder_id=classroom.workspace_folder_id,
            student_username=current_user.username,
            existing_student_folder_id=None,
        )
        if ws_folder_id and member:
            member.workspace_folder_id = ws_folder_id
            db.commit()
            student_folder_id = ws_folder_id

    # Fork
    result = workspace_sync.sync_fork_material(
        teacher_uuid=teacher_uuid,
        student_uuid=student_uuid,
        student_folder_id=student_folder_id,
        source_study_id=source_study_id,
        source_chapter_id=source_chapter_id,
        assignment_title=assignment.title,
    )
    if not result:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to create material fork. Please try again.",
        )

    fork_study_id, fork_chapter_id = result

    fork = MaterialFork(
        assignment_id=assignment_id,
        student_username=current_user.username,
        fork_study_id=fork_study_id,
        fork_chapter_id=fork_chapter_id,
    )
    db.add(fork)
    db.commit()

    return OpenMaterialResponse(
        fork_study_id=fork_study_id,
        fork_chapter_id=fork_chapter_id,
        is_new=True,
    )


# ── List Forks (teacher view) ───────────────────────────────────────────────

@router.get(
    "/classrooms/{classroom_id}/assignments/{assignment_id}/forks",
    response_model=list[ForkItem],
)
def list_forks(
    classroom_id: uuid.UUID,
    assignment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all student forks for a material assignment (teacher/owner only)."""
    classroom = _get_classroom_or_404(db, classroom_id)
    role = _my_role(classroom, current_user.username, db)
    if role not in ("owner", "teacher"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Teacher role required")

    forks = db.execute(
        select(MaterialFork).where(
            MaterialFork.assignment_id == assignment_id,
        ).order_by(MaterialFork.created_at.desc())
    ).scalars().all()

    return [
        ForkItem(
            student_username=f.student_username,
            fork_study_id=f.fork_study_id,
            fork_chapter_id=f.fork_chapter_id,
            created_at=f.created_at.isoformat() if f.created_at else "",
        )
        for f in forks
    ]


# ── Upload Material ──────────────────────────────────────────────────────────

_MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50 MB
_ALLOWED_EXTENSIONS = {
    ".pdf", ".pgn", ".png", ".jpg", ".jpeg", ".gif",
    ".doc", ".docx", ".ppt", ".pptx", ".txt", ".zip",
}


@router.post(
    "/classrooms/{classroom_id}/assignments/{assignment_id}/upload-material",
    status_code=200,
)
def upload_material(
    classroom_id: uuid.UUID,
    assignment_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload a file as material for an assignment. Teacher+ only.
    Stores to R2 and updates assignment source_type/source_ref.
    """
    classroom = _get_classroom_or_404(db, classroom_id)
    role = _my_role(classroom, current_user.username, db)
    if role not in ("owner", "teacher"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Teacher role required")

    assignment = db.execute(
        select(Assignment).where(
            Assignment.id == assignment_id,
            Assignment.classroom_id == classroom_id,
            Assignment.deleted_at.is_(None),
        )
    ).scalar_one_or_none()
    if not assignment:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    # Validate filename extension
    filename = file.filename or "upload"
    ext = ""
    if "." in filename:
        ext = "." + filename.rsplit(".", 1)[1].lower()
    if ext not in _ALLOWED_EXTENSIONS:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"File type '{ext}' not allowed. Allowed: {', '.join(sorted(_ALLOWED_EXTENSIONS))}",
        )

    # Read file content with size check
    content = file.file.read()
    if len(content) > _MAX_UPLOAD_SIZE:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size is {_MAX_UPLOAD_SIZE // (1024*1024)} MB.",
        )

    # Upload to R2
    key = material_key(str(classroom_id), str(assignment_id), filename)
    content_type = file.content_type or "application/octet-stream"

    try:
        storage = get_classroom_storage()
        storage.put_object(key, content, content_type=content_type)
    except Exception:
        logger.exception("Failed to upload material to R2")
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail="Failed to upload file. Please try again.")

    # Update assignment
    source_ref_json = json.dumps({
        "key": key,
        "name": filename,
        "size": len(content),
        "content_type": content_type,
    })
    assignment.source_type = "upload"
    assignment.source_ref = source_ref_json
    db.commit()

    return {"ok": True, "name": filename, "size": len(content)}


# ── Download Material ────────────────────────────────────────────────────────

@router.get(
    "/classrooms/{classroom_id}/assignments/{assignment_id}/download-material",
)
def download_material(
    classroom_id: uuid.UUID,
    assignment_id: uuid.UUID,
    preview: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Download or preview the uploaded material file. Any classroom member.
    Pass ?preview=1 to open inline (images, PDF, text) instead of downloading.
    """
    classroom = _get_classroom_or_404(db, classroom_id)
    _my_role(classroom, current_user.username, db)  # membership check

    assignment = db.execute(
        select(Assignment).where(
            Assignment.id == assignment_id,
            Assignment.classroom_id == classroom_id,
            Assignment.deleted_at.is_(None),
        )
    ).scalar_one_or_none()
    if not assignment:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    if assignment.source_type != "upload" or not assignment.source_ref:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Assignment has no uploaded material")

    try:
        ref = json.loads(assignment.source_ref)
    except (json.JSONDecodeError, TypeError):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid source_ref")

    key = ref.get("key", "")
    filename = ref.get("name", "download")
    content_type = ref.get("content_type", "application/octet-stream")

    try:
        storage = get_classroom_storage()
        data = storage.get_object(key)
    except Exception:
        logger.exception("Failed to download material from R2")
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail="Failed to retrieve file.")

    disposition = "inline" if preview else "attachment"
    return Response(
        content=data,
        media_type=content_type,
        headers={"Content-Disposition": f'{disposition}; filename="{filename}"'},
    )
