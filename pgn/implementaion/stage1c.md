# Stage 1C - FEN 计算与索引

## 约束（必须写在每个 stage 文档开头）
- [ ] 每完成一项任务，必须勾选对应 checkbox。
- [ ] 如果遇到阻塞或不确定，必须直接写明问题，不允许猜测后勾选。
- [ ] 禁止“先勾选后补做”。
- [ ] 禁止谎报进度；我会抽查对比代码。

---

## 本 Stage 目标
实现服务端 FEN 计算能力，并生成 fen_index。

---

## 分计划（Checklist）

### A. 单步 FEN 计算
- [ ] 文件：`backend/core/real_pgn/fen.py`
- [ ] `apply_move(parent_fen, move_san|uci)`：
  - [ ] 使用 python-chess 验证合法性
  - [ ] 返回新 fen / ply / move_number

### B. fen_index 生成
- [ ] `build_fen_index(tree)`：
  - [ ] 遍历 NodeTree
  - [ ] 每个 node_id -> fen
  - [ ] 支持 SetUp/FEN 起始局面

### C. 校验与对照
- [ ] 用 `tests_vectors` 里的样例 PGN 手动比对
- [ ] 记录差异与原因

---

## 输出物（本阶段交付）
- `backend/core/real_pgn/fen.py`

