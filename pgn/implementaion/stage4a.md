# Stage 4A - 产品级 API 检索链路（从 Study 到 PGN）

## 约束（必须写在每个 stage 文档开头）
- [x] 每完成一项任务，必须勾选对应 checkbox。
- [x] 如果遇到阻塞或不确定，必须直接写明问题，不允许猜测后勾选。
- [x] 禁止"先勾选后补做"。
- [x] 禁止谎报进度；我会抽查对比代码。

---

## 本 Stage 目标（产品级）
用户/前端无需理解 R2 key 规则，也能从 study 直接获取 PGN。

---

## 分计划（Checklist）

### A0. 数据来源与对齐（必须理解）
- [x] Postgres（目录与元数据）：
  - [x] `nodes.path` 表示 workspace/folder/study 目录结构
  - [x] `studies.id` == `nodes.id`（study 节点）
  - [x] `chapters.study_id` 关联 study
  - [x] `chapters.id` 是 **R2 key 的唯一对齐 ID**
- [x] R2（棋谱内容）：
  - [x] `chapters/{chapter_id}.pgn` 由 `chapters.id` 生成
  - [x] 绝不使用 `nodes.path` 拼接 R2 key

### A. 找到现有 API 入口（只读定位）
- [x] 打开：`backend/modules/workspace/api/endpoints/studies.py`
- [x] 确认已有 study/chapters API：
  - [x] `GET /{study_id}` 返回 study 与 chapters (第316-387行)
  - [x] `GET /{study_id}/chapters` - 不存在，chapters 包含在 `GET /{study_id}` 响应中
- [x] 确认已有 PGN 导出 API（若存在）：
  - [x] `POST /{study_id}/pgn/export/*` (第597-689行: raw, no-comment, clean, clip)

### B. 定义对外 PGN 读取接口（新增）
- [x] 新增路由：`GET /api/v1/workspace/studies/{study_id}/chapters/{chapter_id}/pgn` (第696-748行)
- [x] 返回结构（明确）：
  - [x] `pgn_text` ✓
  - [x] `pgn_hash` ✓
  - [x] `pgn_size` ✓
  - [x] `last_synced_at` ✓
- [x] 若 PGN 缺失：
  - [x] HTTP 404 ✓ (第734-737行)
  - [x] body 包含 `detail` 与 `chapter_id` ✓

### C. 实现服务调用链（需要明确 import）
- [x] 在 `backend/modules/workspace/api/endpoints/studies.py` 中新增 handler 函数 (第701-748行)
- [x] 必需 import（按现有结构）：
  - [x] `from modules.workspace.db.repos.study_repo import StudyRepository` (第64行)
  - [x] `from modules.workspace.storage.r2_client import R2Client` (第87行)
  - [x] `from modules.workspace.storage.keys import R2Keys` (第86行)
  - [x] `from fastapi import Depends, HTTPException, status` (第7行)
- [x] 依赖注入：
  - [x] 复用已有 `get_study_repository` (第114-117行)
  - [x] 复用已有 `get_r2_client` (第692-693行)

### D. 实际读取流程（产品级链路）
- [x] 根据 `chapter_id` 查询章节：
  - [x] `chapter = await study_repo.get_chapter_by_id(chapter_id)` (第714行)
- [x] 拿到 `r2_key`：
  - [x] 优先用 `chapter.r2_key` (第722行)
  - [x] 若空，fallback `R2Keys.chapter_pgn(chapter_id)` (第722行)
- [x] 通过 R2Client 下载：
  - [x] `pgn_text = r2_client.download_pgn(key)` (第732行)
- [x] 返回携带 `pgn_hash/pgn_size/last_synced_at` (第739-744行)

### E. study/chapters 列表补充状态字段
- [x] 在 `StudyWithChaptersResponse` 或相关 schema 中加入：
  - [x] `pgn_status` (`ready`/`missing`/`error`/`mismatch`) - ChapterResponse 第71行
  - [x] `pgn_hash`, `pgn_size`, `last_synced_at` - ChapterResponse 第69-73行
- [x] 计算 `pgn_status`：
  - [x] 优先使用数据库中的 `pgn_status` 字段 (第367-380行)
  - [x] 若 DB 无状态，根据 `pgn_hash`/`r2_key` 推断

---

## 输出物（本阶段交付）
- [x] 新增 GET PGN API (`GET /{study_id}/chapters/{chapter_id}/pgn`)
- [x] chapter 列表返回 PGN 状态 (pgn_status 字段)
- [x] 统一的读取链路（前端无需拼 R2 key）

---

## 代码位置索引

| 功能 | 文件 | 行号 |
|------|------|------|
| GET /pgn 端点 | studies.py | 696-748 |
| ChapterPgnResponse schema | study.py | 117-123 |
| ChapterResponse (含 pgn_status) | study.py | 54-75 |
| pgn_status 计算逻辑 | studies.py | 364-382 |
| get_r2_client 依赖 | studies.py | 692-693 |

---

## 完成时间
- 2026-01-18
