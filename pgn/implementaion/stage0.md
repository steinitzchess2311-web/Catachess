# Stage 0 - 约束与全局准备（必须先做）

本文件是 Stage 0 的概览。更细拆分见：`stage0a.md`、`stage0b.md`。

## 约束（必须写在每个 stage 文档开头）
- [ ] 每完成一项任务，必须勾选对应 checkbox。
- [ ] 如果遇到阻塞或不确定，必须直接写明问题，不允许猜测后勾选。
- [ ] 禁止“先勾选后补做”。
- [ ] 禁止谎报进度；我会抽查对比代码。

---

## 本 Stage 目标
建立“可执行的迁移落地框架”：明确新增目录、职责边界、依赖约束、回滚策略，以及全局验收基线。

---

## 分计划（Checklist）

### A. 建立迁移基线与可回滚策略
- [ ] 读取并理解 `our_plan.md`，确认“以现有代码为主”的约束。
- [ ] 明确本迁移是“新增 + 切换 + 保留回滚”的策略，不删除旧模块。
- [ ] 记录旧 PGN 相关路径，作为回滚入口：
  - `backend/modules/workspace/pgn/serializer/*`
  - `backend/modules/workspace/domain/services/pgn_sync_service.py`
- [ ] 确认必须保留：`backend/core/new_pgn/*`（PGN 检测与拆分）。
- [ ] 写出回滚点清单（本阶段不改代码，只列清单）：
  - “新 builder 出问题 -> 切回旧 serializer”
  - “新 show API 出问题 -> 前端继续用 mainline 接口”

### B. 确定新增目录与职责边界
- [ ] 新增纯算法层目录：`backend/core/real_pgn/`（仅算法，无 DB/R2）。
- [ ] 新增适配层目录：`backend/modules/workspace/pgn_v2/`（DB/R2 对接）。
- [ ] 不在旧目录塞新逻辑，避免“旧/新混写”。

### C. 现有关键代码入口清单（给后来者）
- [ ] Study 相关入口：`backend/modules/workspace/api/endpoints/studies.py`
- [ ] 变体树表结构：`backend/modules/workspace/db/tables/variations.py`
- [ ] PGN 同步入口：`backend/modules/workspace/domain/services/pgn_sync_service.py`
- [ ] PGN 导入入口：`backend/modules/workspace/domain/services/chapter_import_service.py`
- [ ] R2 Key 规则：`backend/modules/workspace/storage/keys.py`
- [ ] Tagger/Engine 入口：
  - `backend/core/tagger/facade.py`（tag_position）
  - `backend/core/tagger/pipeline/predictor/predictor.py`（预测入口）
  - `backend/core/chess_engine/__init__.py`（get_engine）

### D. 数据与接口约束（必须遵守）
- [ ] DB 结构不改（`variations`/`move_annotations` 保持）。
- [ ] R2 的 `chapters/{chapter_id}.pgn` 继续使用。
- [ ] 新增对象必须为“并行写入”：
  - `chapters/{chapter_id}.tree.json`
  - `chapters/{chapter_id}.fen_index.json`
- [ ] 前端不强制立即切换：必须支持旧接口共存。

### E. 验收基线（迁移成功的最低标准）
- [ ] PGN 能从 NodeTree 生成并能被 lichess/import 读取。
- [ ] ShowDTO 能渲染主线 + 变化 + 注释。
- [ ] 每个节点有 FEN（不再依赖前端传入）。
- [ ] 新/旧系统可回滚切换。

---

## 输出物（本阶段交付）
- 迁移路径清单
- 回滚点清单
- 关键入口清单
- 约束与验收基线
