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
- [ ] 更新 `backend/modules/workspace/storage/keys.py`：
  - [ ] `chapter_tree_json(chapter_id)`
  - [ ] `chapter_fen_index_json(chapter_id)`

### B. 新增 R2 Repo
- [ ] 新建 `backend/modules/workspace/pgn_v2/repo.py`
- [ ] `save_snapshot_pgn(chapter_id, pgn_text)`
- [ ] `save_tree_json(chapter_id, tree_json)`
- [ ] `save_fen_index(chapter_id, fen_index)`

### C. 切换 PGN 同步
- [ ] 修改 `backend/modules/workspace/domain/services/pgn_sync_service.py`：
  - [ ] 调用 `db_to_tree()`
  - [ ] 调用 `builder.build_pgn()`
  - [ ] 调用 `fen.build_fen_index()`
  - [ ] 写入 R2（pgn/tree/fen_index）

### D. 导入服务对接
- [ ] 修改 `backend/modules/workspace/domain/services/chapter_import_service.py`
  - [ ] 解析 PGN -> NodeTree
  - [ ] 写入 DB
  - [ ] 同步 R2

### E. API 路由保持不变
- [ ] 修改 `backend/modules/workspace/api/endpoints/studies.py`
  - [ ] add_move 不再接收前端 fen
  - [ ] 新增 `/show` 与 `/fen`
  - [ ] 旧接口继续保留

---

## 输出物（本阶段交付）
- R2 repo
- 新的 key 规则
- PGN 同步切换
- API 扩展

