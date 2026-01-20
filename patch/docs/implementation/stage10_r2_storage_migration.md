Stage 10 - R2 存储改造（tree.json 为主）

目标
- 将 R2 主存从 PGN 改为 tree.json，PGN 只在导出场景生成。

必须参照的代码路径
- `backend/modules/workspace/pgn_v2/repo.py`
- `backend/modules/workspace/domain/services/pgn_sync_service.py`
- `backend/modules/workspace/storage/keys.py`

硬性约束
- chapter_id 对齐 key，不允许新路径格式。

- Postgres 不变，不新增 tree 字段。

进度记录
- 完成一个 checkbox 立刻打勾。
- 完成整 stage 后必须在 `patch/docs/summary/Codex_stage10.md` 写报告。

Checklist
- [x] 在 `backend/modules/workspace/pgn_v2/repo.py` 将 tree.json 作为核心写路径。
- [x] 将 `save_snapshot_pgn` 改为“导出时调用”，不在编辑同步中调用。
- [x] `pgn_sync_service.sync_chapter_pgn` 改为“只写 tree.json + fen_index（可选）”。
- [x] 移除“每次编辑都写 PGN”的行为（禁用 legacy PGN fallback）。
- [x] R2 key 必须使用 `R2Keys.chapter_tree_json(chapter_id)`。
- [x] 读取路径统一改为 tree.json，缺失则报错。
- [x] 迁移策略文档化：旧 PGN 若存在，首次读取时转换为 tree 并回写。
- [x] 在 `patch/docs/summary/Codex_stage10.md` 写完成报告。
