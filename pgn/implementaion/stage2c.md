# Stage 2C - Tagger 与 Stockfish 分析接入

## 约束（必须写在每个 stage 文档开头）
- [ ] 每完成一项任务，必须勾选对应 checkbox。
- [ ] 如果遇到阻塞或不确定，必须直接写明问题，不允许猜测后勾选。
- [ ] 禁止“先勾选后补做”。
- [ ] 禁止谎报进度；我会抽查对比代码。

---

## 本 Stage 目标
让分析/标签系统使用 fen_index，并输出节点级结果。

---

## 分计划（Checklist）

### A. fen_index 处理器
- [ ] 新建 `backend/core/tagger/analysis/fen_processor.py`
  - [ ] 输入：`chapters/{chapter_id}.fen_index.json`
  - [ ] 输出：node_id + fen 列表

### B. 分析管线扩展
- [ ] 修改 `backend/core/tagger/analysis/pipeline.py`
  - [ ] 新增 `run_fen_index()` 分支
  - [ ] 默认优先使用 fen_index
  - [ ] 保留 pgn_processor 路径

### C. Predictor 扩展
- [ ] 新建 `backend/core/tagger/pipeline/predictor/node_predictor.py`
  - [ ] `predict_node_tags(node_id, fen, move_uci)`
  - [ ] 内部调用 `tag_position()`

### D. 输出落点
- [ ] 选择 tag 输出方式：
  - [ ] DB 新表 `move_tags`（需要 schema 设计）
  - [ ] R2 `chapters/{chapter_id}.tags.json`
- [ ] 明确版本字段与兼容策略（tagger versioning）

---

## 输出物（本阶段交付）
- fen_index 分析入口
- node 级 predictor
- tag 输出落点

