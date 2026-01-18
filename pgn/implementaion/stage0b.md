# Stage 0B - 现有系统地图与依赖清单

## 约束（必须写在每个 stage 文档开头）
- [ ] 每完成一项任务，必须勾选对应 checkbox。
- [ ] 如果遇到阻塞或不确定，必须直接写明问题，不允许猜测后勾选。
- [ ] 禁止“先勾选后补做”。
- [ ] 禁止谎报进度；我会抽查对比代码。

---

## 本 Stage 目标
把现有代码的关键路径列清楚，保证任何新同事只看本文件就知道改哪里。

---

## 分计划（Checklist）

### A. 后端关键入口（必须读）
- [ ] Study API 入口：`backend/modules/workspace/api/endpoints/studies.py`
- [ ] PGN 导入入口：`backend/modules/workspace/domain/services/chapter_import_service.py`
- [ ] PGN 同步入口：`backend/modules/workspace/domain/services/pgn_sync_service.py`
- [ ] 变体树表：`backend/modules/workspace/db/tables/variations.py`
- [ ] R2 key 规则：`backend/modules/workspace/storage/keys.py`

### B. 前端关键入口（必须读）
- [ ] `frontend/ui/modules/study/events/index.ts`

### C. Tagger / Engine 入口（必须读）
- [ ] `backend/core/tagger/facade.py`（tag_position）
- [ ] `backend/core/tagger/pipeline/predictor/predictor.py`（predict_moves）
- [ ] `backend/core/tagger/analysis/pipeline.py`（PGN 分析流程）
- [ ] `backend/core/chess_engine/__init__.py`（get_engine）

### D. 已弃用/待弃用模块（只读对照）
- [ ] `backend/modules/workspace/pgn/serializer/*`
- [ ] `backend/core/chess_basic/pgn/*`

---

## 输出物（本阶段交付）
- 完整“系统地图”清单
- 供新人快速定位的入口索引

