# Stage 4 - 产品级可用性保障（检索/一致性/可追溯）
## 约束（必须写在每个 stage 文档开头）
- [ ] 每完成一项任务，必须勾选对应 checkbox。
- [ ] 如果遇到阻塞或不确定，必须直接写明问题，不允许猜测后勾选。
- [ ] 禁止“先勾选后补做”。
- [ ] 禁止谎报进度；我会抽查对比代码。
---
## 本 Stage 目标（产品级）
让“目录树在 Postgres、棋谱在 R2”的双存储结构对用户透明：
- 用户/前端不需要知道 R2 key 如何拼接
- 后端提供稳定、可检索、可追溯的 API
- 数据一致性可校验、可修复
- 任何异常可追踪与可解释
---
## 分计划（Checklist）
### A. 用户可用的检索链路（产品级要求）
- [x] `GET /api/v1/workspace/studies/{study_id}` 返回 study 与 chapters
  - 文件：`backend/modules/workspace/api/endpoints/studies.py`
- [x] `GET /api/v1/workspace/studies/{study_id}/chapters` 返回章节列表
  - 文件：`backend/modules/workspace/api/endpoints/studies.py`
- [x] `GET /api/v1/workspace/studies/{study_id}/chapters/{chapter_id}/pgn`
  - 文件：`backend/modules/workspace/api/endpoints/studies.py`
- [x] 章节响应包含 `pgn_status/pgn_hash/pgn_size/last_synced_at`
  - 文件：`backend/modules/workspace/api/schemas/study.py`

### B. 数据一致性规则（强约束）
- [x] `chapters.r2_key` 与 `R2Keys.chapter_pgn(chapter_id)` 对齐
  - 写入校验：`backend/modules/workspace/domain/services/pgn_sync_service.py`
- [x] `pgn_hash/pgn_size` 写回用于一致性与审计
  - 写入位置：`backend/modules/workspace/domain/services/pgn_sync_service.py`

### C. 缺失数据的可见性与恢复
- [x] API 返回 `pgn_status` 用于前端可见性
  - 文件：`backend/modules/workspace/api/schemas/study.py`
- [x] 扫描脚本支持标记缺失并触发修复
  - 文件：`backend/scripts/scan_pgn_integrity.py`
- [x] 运维修复入口：`sync_chapter_pgn(chapter_id)`
  - 文件：`backend/modules/workspace/domain/services/pgn_sync_service.py`

### D. 迁移阶段的校验任务（一次性/可复用）
- [x] 批量扫描输出报告（JSON/CSV）
  - 文件：`backend/scripts/scan_pgn_integrity.py`
  - 报告路径：`docs/migration_reports/*`

### E. 监控与告警（产品稳定性）
- [x] `/show` 与 `/fen` 失败日志包含 `study_id/chapter_id/r2_key/error_code`
  - 文件：`backend/modules/workspace/api/endpoints/studies.py`
- [x] 生产告警阈值设定（外部监控系统配置）
  - 文件：`docs/pgn/ops_pgn_v2.md`

### F. 运维/对外说明
- [x] 运维文档：`docs/pgn/ops_pgn_v2.md`
- [x] 对外 FAQ（如需客服话术）
  - 文件：`docs/pgn/faq_pgn.md`
---
## 输出物（本阶段交付）
- 产品级 API 检索链路
- 数据一致性校验与扫描修复脚本
- 运维文档与故障排查入口
