# Stage 2A - DB 适配层

## 约束（必须写在每个 stage 文档开头）
- [ ] 每完成一项任务，必须勾选对应 checkbox。
- [ ] 如果遇到阻塞或不确定，必须直接写明问题，不允许猜测后勾选。
- [ ] 禁止“先勾选后补做”。
- [ ] 禁止谎报进度；我会抽查对比代码。

---

## 本 Stage 目标
完成 DB <-> NodeTree 的适配，不改表结构。

---

## 分计划（Checklist）

### A. DB -> NodeTree
- [x] 文件：`backend/modules/workspace/pgn_v2/adapters.py`
- [x] `db_to_tree(variations, annotations)`：
  - [x] parent_id/rank 正确映射
  - [x] comment/nag 正确映射
  - [x] headers/result 由 Chapter/PGN 来源补齐（不缺失）

### B. NodeTree -> DB 变更
- [x] `tree_to_db_changes(tree)`：
  - [x] 仅输出增量操作（新增 move / 更新 comment）
  - [x] 不做全量重建
  - [x] 支持 rank 与 variation

### C. 错误处理
- [x] 如果 parent 不存在，返回明确错误 (ParentNotFoundError)
- [x] 如果 move 不合法，返回明确错误 (InvalidMoveError)

---

## 输出物（本阶段交付）
- `backend/modules/workspace/pgn_v2/adapters.py`

