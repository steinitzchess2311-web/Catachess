# Stage 1B - PGN Parser 与 ShowDTO

## 约束（必须写在每个 stage 文档开头）
- [ ] 每完成一项任务，必须勾选对应 checkbox。
- [ ] 如果遇到阻塞或不确定，必须直接写明问题，不允许猜测后勾选。
- [ ] 禁止“先勾选后补做”。
- [ ] 禁止谎报进度；我会抽查对比代码。

---

## 本 Stage 目标
实现 PGN -> NodeTree 的解析，并生成前端可用 ShowDTO。

---

## 分计划（Checklist）

### A. PGN Parser
- [ ] 文件：`backend/core/real_pgn/parser.py`
- [ ] `parse_pgn(pgn_text)`：
  - [ ] 支持 headers 与 result
  - [ ] 支持 variations / comments / NAG
  - [ ] 支持 SetUp/FEN
  - [ ] 生成稳定 node_id（避免依赖顺序）
  - [ ] 遇到非法 PGN 抛异常

### B. ShowDTO
- [ ] 文件：`backend/core/real_pgn/show.py`
- [ ] `build_show(tree)`：
  - [ ] 输出 headers 数组
  - [ ] 输出 nodes dict
  - [ ] 输出 render token 流
  - [ ] token 支持 move/comment/variation_start/variation_end
- [ ] 确保前端无需二次解析即可渲染

---

## 输出物（本阶段交付）
- `backend/core/real_pgn/parser.py`
- `backend/core/real_pgn/show.py`

