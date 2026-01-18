# Stage 4C - 缺失数据恢复与批量扫描

## 约束（必须写在每个 stage 文档开头）
- [ ] 每完成一项任务，必须勾选对应 checkbox。
- [ ] 如果遇到阻塞或不确定，必须直接写明问题，不允许猜测后勾选。
- [ ] 禁止“先勾选后补做”。
- [ ] 禁止谎报进度；我会抽查对比代码。

---

## 本 Stage 目标（产品级）
即使 R2 中的 PGN 丢失，也能被发现并可一键修复。

---

## 分计划（Checklist）

### A. 缺失 PGN 的检测逻辑
- [ ] 新增函数：`check_pgn_exists(chapter_id)`
- [ ] 推荐位置：`backend/modules/workspace/pgn_v2/repo.py`
- [ ] 必需 import：
  - [ ] `from modules.workspace.storage.keys import R2Keys`
  - [ ] `from modules.workspace.storage.r2_client import R2Client`
- [ ] 实现：
  - [ ] `key = R2Keys.chapter_pgn(chapter_id)`
  - [ ] `exists = r2_client.exists(key)`
  - [ ] 返回 bool

### B. 重建 PGN 的内部命令
- [ ] 新增管理函数：`rebuild_chapter_pgn(chapter_id)`
- [ ] 推荐位置：`backend/modules/workspace/domain/services/pgn_sync_service.py`
- [ ] 依赖链路：
  - [ ] 从 DB 取 variations/annotations
  - [ ] `db_to_tree()` -> NodeTree
  - [ ] `builder.build_pgn()` -> pgn_text
  - [ ] 写回 R2
- [ ] 需要 import：
  - [ ] `from modules.workspace.db.repos.variation_repo import VariationRepository`
  - [ ] `from modules.workspace.pgn_v2.adapters import db_to_tree`
  - [ ] `from core.real_pgn.builder import build_pgn`

### C. 批量扫描脚本（一次性/可重复）
- [ ] 新增脚本：`backend/scripts/scan_pgn_integrity.py`
- [ ] 脚本功能：
  - [ ] 遍历 studies -> chapters
  - [ ] 校验 r2_key 一致
  - [ ] 检测 R2 是否存在
  - [ ] 输出 JSON/CSV 报告
- [ ] 必需 import：
  - [ ] `from modules.workspace.db.repos.study_repo import StudyRepository`
  - [ ] `from modules.workspace.storage.r2_client import R2Client`
  - [ ] `from modules.workspace.storage.keys import R2Keys`

### D. API 反馈（产品级）
- [ ] 若 PGN 缺失：
  - [ ] API 返回 `pgn_status = missing`
  - [ ] 前端显示“重建”入口（只对管理员）

---

## 输出物（本阶段交付）
- 缺失检测逻辑
- 重建 PGN 工具
- 批量扫描脚本与报告

