# Stage 4B - 数据一致性与自动修复（chapter_id ↔ r2_key）

## 约束（必须写在每个 stage 文档开头）
- [ ] 每完成一项任务，必须勾选对应 checkbox。
- [ ] 如果遇到阻塞或不确定，必须直接写明问题，不允许猜测后勾选。
- [ ] 禁止“先勾选后补做”。
- [ ] 禁止谎报进度；我会抽查对比代码。

---

## 本 Stage 目标（产品级）
确保 R2 中的 PGN key 与 Postgres 中的 chapter_id 一致，避免读取错位。

---

## 分计划（Checklist）

### A. 新增一致性校验函数（代码层）
- [ ] 在 `backend/modules/workspace/pgn_v2/repo.py` 中新增：
  - [ ] `ensure_chapter_key(chapter) -> str`
- [ ] 必需 import：
  - [ ] `from modules.workspace.storage.keys import R2Keys`
  - [ ] `import logging`
- [ ] 逻辑：
  - [ ] 计算 `expected = R2Keys.chapter_pgn(chapter.id)`
  - [ ] 若 `chapter.r2_key` 为空或不等于 expected -> 记录 warning
  - [ ] 自动回填：`chapter.r2_key = expected`
  - [ ] 返回最终 key

### B. 在 PGN 同步中强制校验
- [ ] 文件：`backend/modules/workspace/domain/services/pgn_sync_service.py`
- [ ] 在写 R2 前调用 `ensure_chapter_key(chapter)`
- [ ] 记录日志字段：`study_id`, `chapter_id`, `r2_key`

### C. 在导入流程中强制校验
- [ ] 文件：`backend/modules/workspace/domain/services/chapter_import_service.py`
- [ ] 创建 chapter 后立即调用 `ensure_chapter_key()`
- [ ] 确保写入 R2 前 key 已一致

### D. 对外状态字段（API 层）
- [ ] 在 chapter 输出 schema 中暴露：
  - [ ] `r2_key`
  - [ ] `pgn_hash`
  - [ ] `pgn_size`
  - [ ] `last_synced_at`
- [ ] 如果 `r2_key` 不一致（理论上不会）：
  - [ ] 标记 `pgn_status = mismatch`

---

## 输出物（本阶段交付）
- 统一 key 校验/回填逻辑
- PGN 同步与导入流程具备强一致性
- API 层提供一致性状态

