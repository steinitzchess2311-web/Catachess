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
- [x] 新建 `backend/core/tagger/analysis/fen_processor.py`
  - [x] 输入：`chapters/{chapter_id}.fen_index.json`
  - [x] 输出：node_id + fen 列表 (NodeFenEntry)

### B. 分析管线扩展
- [x] FenIndexProcessor 可从 R2 加载 fen_index（load_and_process 方法）
  - [x] 优先使用 fen_index
  - [x] 保留 tree_json 回退路径

### C. Predictor 扩展
- [x] 新建 `backend/core/tagger/pipeline/predictor/node_predictor.py`
  - [x] `predict_node_tags(node_id, fen, move_uci)` -> NodeTagResult
  - [x] `predict_batch(nodes)` 批量处理
  - [x] 内部调用 TaggingPipeline.evaluate()

### D. 输出落点
- [x] R2 输出方式：
  - [x] R2 key: `chapters/{chapter_id}.tags.json`
  - [x] PgnV2Repo.save_tags_json() 方法
  - [x] PgnV2Repo.load_tags_json() 方法
- [ ] 版本字段与兼容策略（待后续需求明确）

---

## 输出物（本阶段交付）
- fen_index 分析入口
- node 级 predictor
- tag 输出落点

