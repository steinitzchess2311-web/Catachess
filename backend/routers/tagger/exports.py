"""
Tagger Exports Router - 导出 API

导出参数（来自 Stage 05）：
- upload_ids（可选，逗号分隔）
- from / to（可选，ISO 时间）
"""
import uuid
import csv
import json
from io import StringIO
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from core.db.deps import get_db
from modules.tagger import TaggerService

router = APIRouter()


def get_service(db: Session = Depends(get_db)) -> TaggerService:
    return TaggerService(db)


@router.get("/players/{player_id}/exports")
async def export_stats(
    player_id: uuid.UUID,
    format: str = Query("csv", pattern="^(csv|json)$"),
    upload_ids: Optional[str] = None,
    from_date: Optional[datetime] = Query(None, alias="from"),
    to_date: Optional[datetime] = Query(None, alias="to"),
    svc: TaggerService = Depends(get_service),
):
    """导出统计（支持范围过滤）"""
    if not svc.get_player(player_id):
        raise HTTPException(404, "Player not found")

    uid_list = [uuid.UUID(x.strip()) for x in upload_ids.split(",") if x.strip()] if upload_ids else None
    stats = svc.get_stats_filtered(player_id, uid_list, from_date, to_date)

    data = [
        {
            "scope": s.scope,
            "tag_name": s.tag_name,
            "tag_count": s.tag_count,
            "total_positions": s.total_positions,
            "percentage": (s.tag_count / s.total_positions * 100) if s.total_positions else 0,
        }
        for s in stats
    ]

    if format == "json":
        return StreamingResponse(
            iter([json.dumps(data, indent=2, default=str)]),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={player_id}_stats.json"},
        )

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["scope", "tag_name", "tag_count", "total_positions", "percentage"])
    for d in data:
        writer.writerow([d["scope"], d["tag_name"], d["tag_count"], d["total_positions"], f"{d['percentage']:.2f}"])
    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={player_id}_stats.csv"},
    )
