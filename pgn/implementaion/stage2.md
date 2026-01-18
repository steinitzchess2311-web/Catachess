# Stage 2 - 系统接入与迁移（DB/R2/API/Tagger/Engine）

本文件是 Stage 2 的概览。更细拆分见：`stage2a.md`、`stage2b.md`、`stage2c.md`、`stage2d.md`。

## 约束（必须写在每个 stage 文档开头）
- [ ] 每完成一项任务，必须勾选对应 checkbox。
- [ ] 如果遇到阻塞或不确定，必须直接写明问题，不允许猜测后勾选。
- [ ] 禁止“先勾选后补做”。
- [ ] 禁止谎报进度；我会抽查对比代码。

---

## 本 Stage 目标
把 Stage1 的核心能力接入现有系统：
- DB 变体树（variations/move_annotations）
- R2 存储（chapters/*.pgn + tree/fen_index）
- API 路由（保持不破坏旧接口）
- Tagger/Stockfish 分析（使用新 fen_index）
- 前端切换 ShowDTO

---

## 分计划（Checklist）

### A. DB 适配层（NodeTree <-> DB）
- [ ] 新建 `backend/modules/workspace/pgn_v2/adapters.py`。
- [ ] 实现 `db_to_tree(variations, annotations) -> NodeTree`：
  - [ ] 映射 `Variation` -> `PgnNode`（san/uci/fen/move_number/parent_id/rank）。
  - [ ] 映射 `MoveAnnotation` -> comment_after + nags。
  - [ ] 处理 root 与 variations rank。
- [ ] 实现 `tree_to_db_changes(tree) -> operations`：
  - [ ] 新增 move -> 写 `variations`。
  - [ ] 新增 comment/nag -> 写 `move_annotations`。
  - [ ] 仅输出最小变更，避免全量重建。

### B. R2 输出与 Key 规则（沿用现有 key）
- [ ] 更新 `backend/modules/workspace/storage/keys.py`：
  - [ ] 新增 `chapter_tree_json(chapter_id)`。
  - [ ] 新增 `chapter_fen_index_json(chapter_id)`。
- [ ] 新建 `backend/modules/workspace/pgn_v2/repo.py`：
  - [ ] `save_snapshot_pgn(chapter_id, pgn_text)` -> 上传 `chapters/{chapter_id}.pgn`。
  - [ ] `save_tree_json(chapter_id, tree_json)` -> 上传 `chapters/{chapter_id}.tree.json`。
  - [ ] `save_fen_index(chapter_id, fen_index)` -> 上传 `chapters/{chapter_id}.fen_index.json`。

### C. PGN 同步服务切换
- [ ] 修改 `backend/modules/workspace/domain/services/pgn_sync_service.py`：
  - [ ] 使用 `pgn_v2.adapters.db_to_tree()` 构造 NodeTree。
  - [ ] 使用 `backend/core/real_pgn/builder.py` 生成 PGN。
  - [ ] 使用 `backend/core/real_pgn/fen.py` 生成 fen_index。
  - [ ] 写入 R2：pgn + tree.json + fen_index.json。
- [ ] 保留旧 serializer 用于对比（不要删）。

### D. 导入服务改造（PGN -> DB -> R2）
- [ ] 修改 `backend/modules/workspace/domain/services/chapter_import_service.py`：
  - [ ] 导入 PGN 后，调用 `backend/core/real_pgn/parser.py` -> NodeTree。
  - [ ] 使用 `pgn_v2.adapters.tree_to_db_changes()` 写入 DB。
  - [ ] 导入完成后触发 `pgn_sync_service`。
  - [ ] 继续用 `backend/core/new_pgn` 做拆分检测。

### E. API 接口保持不变，内部切换
- [ ] `backend/modules/workspace/api/endpoints/studies.py`：
  - [ ] `add_move` 不再接受前端传 fen（后端计算）。
  - [ ] `add_move` 内部调用 `real_pgn/fen.py` 计算 fen + ply。
  - [ ] 新增 `/show`：返回 ShowDTO。
  - [ ] 新增 `/fen`：按 node_id 返回 fen。
  - [ ] 保留旧 mainline 接口（前端可回退）。

### F. Tagger/Stockfish 接入（按现有代码路径）
- [ ] 新增 `backend/core/tagger/analysis/fen_processor.py`：
  - [ ] 输入：`chapters/{chapter_id}.fen_index.json`。
  - [ ] 输出：node_id + fen 列表。
- [ ] 修改 `backend/core/tagger/analysis/pipeline.py`：
  - [ ] 新增 `run_fen_index()` 分支。
  - [ ] 优先使用 fen_index，保留 PGN 文件模式。
- [ ] 新增 `backend/core/tagger/pipeline/predictor/node_predictor.py`：
  - [ ] `predict_node_tags(node_id, fen, move_uci)`。
  - [ ] 内部调用 `tag_position()`。
- [ ] 定义 tag 输出落点（二选一）：
  - [ ] DB 新表（若选择 DB，需设计 schema）
  - [ ] R2 `chapters/{chapter_id}.tags.json`

### G. Frontend 切换（可回滚）
- [ ] 更新 `frontend/ui/modules/study/events/index.ts`：
  - [ ] 拉取 `/show` 并渲染。
  - [ ] 点击 move 时使用 DTO 内 fen。
  - [ ] 保留 mainline 渲染的 fallback。

### H. 回归对比与验收
- [ ] 使用 `backend/modules/workspace/pgn/tests_vectors/*` 对比旧/新输出一致性。
- [ ] 手动验证：
  - [ ] 复杂变例渲染正确
  - [ ] 注释 + NAG 正确
  - [ ] 非标准起始局面正确
- [ ] 记录差异与原因（必须写明）。

---

## 输出物（本阶段交付）
- DB 适配层：`backend/modules/workspace/pgn_v2/adapters.py`
- R2 Repo：`backend/modules/workspace/pgn_v2/repo.py`
- 改造后的 `pgn_sync_service.py` 与 `chapter_import_service.py`
- 新增 `/show` `/fen` API
- 新的 fen_index 分析通路
- 前端 ShowDTO 渲染
