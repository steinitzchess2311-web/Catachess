"""
Tagger upload logging helpers.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from models.tagger import PgnUpload

_LOG_LIMIT = 500


def append_upload_log(
    db: Session,
    upload: PgnUpload,
    message: str,
    level: str = "info",
    extra: dict[str, Any] | None = None,
) -> None:
    """
    Append a log entry to upload.checkpoint_state["logs"].
    Keeps only the most recent _LOG_LIMIT entries.
    """
    state = dict(upload.checkpoint_state or {})
    logs = list(state.get("logs", []))
    entry = {
        "ts": datetime.utcnow().isoformat(),
        "level": level,
        "message": message,
    }
    if extra:
        entry["extra"] = extra
    logs.append(entry)
    if len(logs) > _LOG_LIMIT:
        logs = logs[-_LOG_LIMIT:]
    state["logs"] = logs
    upload.checkpoint_state = state
    db.commit()
