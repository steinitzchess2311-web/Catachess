"""
R2 key helpers for classroom materials.

Key format:
    materials/{classroom_id}/{assignment_id}/{uuid8}_{safe_filename}

The short uuid prefix prevents collisions if the same filename is
re-uploaded after a delete.
"""
import re
import uuid


def material_key(classroom_id: str, assignment_id: str, filename: str) -> str:
    safe = _safe_filename(filename)
    short_id = uuid.uuid4().hex[:8]
    return f"materials/{classroom_id}/{assignment_id}/{short_id}_{safe}"


def _safe_filename(name: str) -> str:
    """Sanitise a filename for use in an R2 key."""
    # Keep only alphanumeric, dots, hyphens, underscores
    safe = re.sub(r'[^\w.\-]', '_', name)
    # Collapse runs of underscores
    safe = re.sub(r'_+', '_', safe).strip('_')
    return safe[:120] or 'file'
