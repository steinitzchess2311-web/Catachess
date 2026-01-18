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
- [ ] 运行 `backend/scripts/scan_pgn_integrity.py`（见 stage4c.md）
- [ ] 输出报告（JSON/CSV）
- [ ] 记录不一致数量与修复比例

### B. 修复规则（必须一致）
- [ ] `chapter.r2_key` != `R2Keys.chapter_pgn(chapter_id)` -> 回填
- [ ] R2 404 -> 标记 `pgn_status = missing`
- [ ] hash/size 不一致 -> 重新同步 PGN

### C. 迁移完成条件
- [ ] r2_key 不一致数量 == 0
- [ ] missing PGN 已修复或明确标记
- [ ] 记录迁移日期与操作人

---

## 输出物（本阶段交付）
- 全量扫描报告
- 修复日志
- 迁移验收记录

