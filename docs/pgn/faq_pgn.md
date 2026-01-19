# PGN v2 FAQ

## 为什么 PGN 显示为空？
- 章节没有走子，属于空章节（`pgn_status=ready` 但无内容）
- R2 产物丢失（`pgn_status=missing`）
- 同步失败或被中断（`pgn_status=error`）

## 如何恢复？
- 运行修复入口：`sync_chapter_pgn(chapter_id)`
- 如果是批量问题，运行扫描脚本：`backend/scripts/scan_pgn_integrity.py`

## 前端需要拼接 R2 key 吗？
不需要。前端只调用 API：
- `GET /api/v1/workspace/studies/{study_id}`
- `GET /api/v1/workspace/studies/{study_id}/chapters`
- `GET /api/v1/workspace/studies/{study_id}/chapters/{chapter_id}/pgn`

## 为什么会看到 404？
- 章节不存在或没有权限
- PGN 在 R2 缺失（后端会返回 404 + detail）
