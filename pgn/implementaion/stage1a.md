# Stage 1A - NodeTree 与 PGN Builder

## 约束（必须写在每个 stage 文档开头）
- [ ] 每完成一项任务，必须勾选对应 checkbox。
- [ ] 如果遇到阻塞或不确定，必须直接写明问题，不允许猜测后勾选。
- [ ] 禁止“先勾选后补做”。
- [ ] 禁止谎报进度；我会抽查对比代码。

---

## 本 Stage 目标
构建 NodeTree 数据结构与 PGN Builder，保证输出符合标准 PGN。

---

## 分计划（Checklist）

### A. NodeTree 数据结构
- [ ] 文件：`backend/core/real_pgn/models.py`
- [ ] 定义 `PgnNode`：
  - [ ] node_id, parent_id
  - [ ] san, uci
  - [ ] ply, move_number
  - [ ] comment_before, comment_after
  - [ ] nags（list[int]）
  - [ ] main_child, variations
  - [ ] fen
- [ ] 定义 `NodeTree`：
  - [ ] nodes dict
  - [ ] root_id
  - [ ] headers/meta
- [ ] 定义 `GameMeta`：
  - [ ] headers
  - [ ] result
  - [ ] setup_fen
  - [ ] startpos 处理

### B. PGN Builder
- [ ] 文件：`backend/core/real_pgn/builder.py`
- [ ] `build_pgn(tree)` 输出标准 PGN
  - [ ] headers 顺序（Event/Site/Date/White/Black/Result）
  - [ ] SetUp/FEN 支持
  - [ ] movetext：
    - [ ] 白方带回合号
    - [ ] 黑方起手 1...
    - [ ] variations 用括号
    - [ ] NAG 用 $x
    - [ ] comment_before / comment_after 用 `{...}`
  - [ ] 结尾 Result
- [ ] 与 `backend/modules/workspace/pgn/serializer/to_pgn.py` 对照一致性

---

## 输出物（本阶段交付）
- `backend/core/real_pgn/models.py`
- `backend/core/real_pgn/builder.py`

