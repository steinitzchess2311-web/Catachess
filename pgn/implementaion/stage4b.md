# Stage 4B - 数据一致性与自动修复（chapter_id ↔ r2_key）

## 约束（必须写在每个 stage 文档开头）
- [x] 每完成一项任务，必须勾选对应 checkbox。
- [x] 如果遇到阻塞或不确定，必须直接写明问题，不允许猜测后勾选。
- [x] 禁止"先勾选后补做"。
- [x] 禁止谎报进度；我会抽查对比代码。

---

## 本 Stage 目标（产品级）
确保 R2 中的 PGN key 与 Postgres 中的 chapter_id 一致，避免读取错位。

---

## 分计划（Checklist）

### A0. 对齐规则（必须牢记）
- [x] Postgres：`chapters.id` 是唯一对齐 ID
- [x] R2：`chapters/{chapter_id}.pgn` 必须与 `chapters.r2_key` 一致
- [x] `nodes.path` 只用于目录展示，不参与 R2 key 生成

### A. 新增一致性校验函数（代码层）
- [x] 在 `backend/modules/workspace/pgn_v2/repo.py` 中新增：
  - [x] `ensure_chapter_key(chapter) -> str` (第315-343行)
  - [x] `validate_chapter_r2_key(chapter, expected_key) -> bool` (第346-367行)
  - [x] `backfill_chapter_r2_key(chapter) -> str` (第370-382行)
- [x] 必需 import：
  - [x] `from modules.workspace.storage.keys import R2Keys` (第15行)
  - [x] `import logging` (第11行)
- [x] 逻辑：
  - [x] 计算 `expected = R2Keys.chapter_pgn(chapter.id)`
  - [x] 若 `chapter.r2_key` 为空或不等于 expected -> 记录 warning
  - [x] 自动回填：返回 `expected` key
  - [x] 返回最终 key

### B. 在 PGN 同步中强制校验
- [x] 文件：`backend/modules/workspace/domain/services/pgn_sync_service.py`
- [x] 在写 R2 前调用校验 (第64-68行)：
  ```python
  if not validate_chapter_r2_key(chapter):
      standard_key = backfill_chapter_r2_key(chapter)
      chapter.r2_key = standard_key
      await self.study_repo.update_chapter(chapter)
  ```
- [x] 记录日志字段：`study_id`, `chapter_id`, `r2_key` (第142-150行, 第218-226行)

### C. 在导入流程中强制校验
- [x] 文件：`backend/modules/workspace/domain/services/chapter_import_service.py`
- [x] 创建 chapter 后立即调用校验 (第423-426行)：
  ```python
  if not validate_chapter_r2_key(chapter):
      chapter.r2_key = backfill_chapter_r2_key(chapter)
      await self.study_repo.update_chapter(chapter)
  ```
- [x] 确保写入 R2 前 key 已一致

### D. 对外状态字段（API 层）
- [x] 在 chapter 输出 schema 中暴露 (`api/schemas/study.py` ChapterResponse 第54-75行)：
  - [x] `r2_key` (第68行)
  - [x] `pgn_hash` (第69行)
  - [x] `pgn_size` (第70行)
  - [x] `last_synced_at` (第73行)
- [x] 如果 `r2_key` 不一致（理论上不会）：
  - [x] 扫描脚本标记 `pgn_status = mismatch` (`scan_pgn_integrity.py` 第221-223行)

---

## 输出物（本阶段交付）
- [x] 统一 key 校验/回填逻辑 (`ensure_chapter_key`, `validate_chapter_r2_key`, `backfill_chapter_r2_key`)
- [x] PGN 同步与导入流程具备强一致性
- [x] API 层提供一致性状态 (`r2_key`, `pgn_status` 等字段)

---

## 代码位置索引

| 功能 | 文件 | 行号 |
|------|------|------|
| ensure_chapter_key | pgn_v2/repo.py | 315-343 |
| validate_chapter_r2_key | pgn_v2/repo.py | 346-367 |
| backfill_chapter_r2_key | pgn_v2/repo.py | 370-382 |
| 同步时校验 | pgn_sync_service.py | 64-68 |
| 导入时校验 | chapter_import_service.py | 423-426 |
| ChapterResponse schema | api/schemas/study.py | 54-75 |
| 扫描 mismatch 标记 | scan_pgn_integrity.py | 221-223 |

---

## 完成时间
- 2026-01-18
