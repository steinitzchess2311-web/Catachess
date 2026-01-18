# Stage 2B - R2 同步与 API 切换

## 约束（必须写在每个 stage 文档开头）
- [ ] 每完成一项任务，必须勾选对应 checkbox。
- [ ] 如果遇到阻塞或不确定，必须直接写明问题，不允许猜测后勾选。
- [ ] 禁止“先勾选后补做”。
- [ ] 禁止谎报进度；我会抽查对比代码。

---

## 本 Stage 目标
把新 NodeTree 产物写入 R2，并保持 API 路由不变。

---

## 分计划（Checklist）

### A. R2 Key 扩展
- [x] 更新 `backend/modules/workspace/storage/keys.py`：
  - [x] `chapter_tree_json(chapter_id)`
  - [x] `chapter_fen_index_json(chapter_id)`

### B. 新增 R2 Repo
- [x] 新建 `backend/modules/workspace/pgn_v2/repo.py`
- [x] `save_snapshot_pgn(chapter_id, pgn_text)`
- [x] `save_tree_json(chapter_id, tree_json)`
- [x] `save_fen_index(chapter_id, fen_index)`

### B1. ID 对齐校验与回填（必须加）
- [x] 新增一致性校验：`chapter.r2_key == R2Keys.chapter_pgn(chapter_id)` (validate_chapter_r2_key)
- [x] 若不一致：
  - [x] 记录日志/告警（至少 warning）
  - [x] 回填为标准 key（迁移阶段允许自动修复）(backfill_chapter_r2_key)
- [x] 在 PGN 同步时执行校验（避免后续写错位置）

### C. 切换 PGN 同步
- [x] 修改 `backend/modules/workspace/domain/services/pgn_sync_service.py`：
  - [x] 调用 `db_to_tree()`
  - [x] 调用 `builder.build_pgn()`
  - [x] 调用 `fen.build_fen_index()`
  - [x] 写入 R2（pgn/tree/fen_index）

### D. 导入服务对接
- [x] 修改 `backend/modules/workspace/domain/services/chapter_import_service.py`
  - [x] 解析 PGN -> NodeTree (parse_pgn)
  - [x] 写入 DB (tree_to_db_changes -> variation_repo)
  - [x] 同步 R2 (PgnV2Repo)

### E. API 路由保持不变
- [x] 修改 `backend/modules/workspace/api/endpoints/studies.py`
  - [ ] add_move 不再接收前端 fen (需要后续更新 MoveCreate schema)
  - [x] 新增 `/show` 端点
  - [x] 新增 `/fen` 端点
  - [x] 旧接口继续保留

---

## 输出物（本阶段交付）
- R2 repo
- 新的 key 规则
- PGN 同步切换
- API 扩展
