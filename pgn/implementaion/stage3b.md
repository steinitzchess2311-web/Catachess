# Stage 3B - 数据迁移与一致性验证（全量）

## 约束（必须写在每个 stage 文档开头）
- [ ] 每完成一项任务，必须勾选对应 checkbox。
- [ ] 如果遇到阻塞或不确定，必须直接写明问题，不允许猜测后勾选。
- [ ] 禁止“先勾选后补做”。
- [ ] 禁止谎报进度；我会抽查对比代码。

---

## 本 Stage 目标（产品级）
保证 Postgres 与 R2 的数据完全对齐，避免“目录有、PGN 无”或“PGN 指错 key”。

---

## 分计划（Checklist）

### A. 扫描脚本执行
- [x] 运行 `backend/scripts/scan_pgn_integrity.py`（见 stage4c.md）
  - 记录见：`docs/migration_reports/migration_scan_report.txt`
  - 命令与环境见：`docs/migration_reports/migration_acceptance.md`
- [x] 输出报告（JSON/CSV）
  - JSON 汇总：`docs/migration_reports/migration_scan_summary.json`
  - 原始输出：`docs/migration_reports/migration_scan_report.txt`
- [x] 记录不一致数量与修复比例
  - 汇总见：`docs/migration_reports/migration_acceptance.md`（repair ratio 0/85）

### B. 修复规则（必须一致）
- [x] `chapter.r2_key` != `R2Keys.chapter_pgn(chapter_id)` -> 回填
  - 扫描脚本已实现回填；本次扫描 mismatch=0。
- [x] R2 404 -> 标记 `pgn_status = missing`
  - 本次扫描未出现缺失；报告见 `docs/migration_reports/migration_scan_report.txt`。
- [x] hash/size 不一致 -> 重新同步 PGN
  - 脚本在缺失/元数据缺失时触发 resync；本次无不一致。

### C. 迁移完成条件
- [x] r2_key 不一致数量 == 0
  - 见 `docs/migration_reports/migration_scan_report.txt`。
- [x] missing PGN 已修复或明确标记
  - 见 `docs/migration_reports/migration_scan_report.txt`（missing=0）。
- [x] 记录迁移日期与操作人
  - 见 `docs/migration_reports/migration_acceptance.md`（Operator: codex）。

---

## 输出物（本阶段交付）
- 全量扫描报告
- 修复日志
- 迁移验收记录
