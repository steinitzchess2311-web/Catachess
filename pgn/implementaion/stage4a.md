# Stage 4A - 产品级 API 检索链路（从 Study 到 PGN）

## 约束（必须写在每个 stage 文档开头）
- [ ] 每完成一项任务，必须勾选对应 checkbox。
- [ ] 如果遇到阻塞或不确定，必须直接写明问题，不允许猜测后勾选。
- [ ] 禁止“先勾选后补做”。
- [ ] 禁止谎报进度；我会抽查对比代码。

---

## 本 Stage 目标（产品级）
用户/前端无需理解 R2 key 规则，也能从 study 直接获取 PGN。

---

## 分计划（Checklist）

### A. 找到现有 API 入口（只读定位）
- [ ] 打开：`backend/modules/workspace/api/endpoints/studies.py`
- [ ] 确认已有 study/chapters API：
  - [ ] `GET /{study_id}` 返回 study 与 chapters
  - [ ] `GET /{study_id}/chapters` 返回章节列表
- [ ] 确认已有 PGN 导出 API（若存在）：
  - [ ] `POST /{study_id}/pgn/export/*` 或类似

### B. 定义对外 PGN 读取接口（新增）
- [ ] 新增路由：`GET /api/v1/workspace/studies/{study_id}/chapters/{chapter_id}/pgn`
- [ ] 返回结构（明确）：
  - [ ] `pgn_text`
  - [ ] `pgn_hash`
  - [ ] `pgn_size`
  - [ ] `last_synced_at`
- [ ] 若 PGN 缺失：
  - [ ] HTTP 404
  - [ ] body 包含 `detail` 与 `chapter_id`

### C. 实现服务调用链（需要明确 import）
- [ ] 在 `backend/modules/workspace/api/endpoints/studies.py` 中新增 handler 函数
- [ ] 必需 import（按现有结构）：
  - [ ] `from modules.workspace.db.repos.study_repo import StudyRepository`
  - [ ] `from modules.workspace.storage.r2_client import R2Client`
  - [ ] `from modules.workspace.storage.keys import R2Keys`
  - [ ] `from fastapi import Depends, HTTPException, status`
- [ ] 依赖注入：
  - [ ] 复用已有 `get_study_repository`（若存在）
  - [ ] 复用已有 `get_r2_client`（若存在，路径同目录依赖文件）

### D. 实际读取流程（产品级链路）
- [ ] 根据 `chapter_id` 查询章节：
  - [ ] `chapter = await study_repo.get_chapter_by_id(chapter_id)`
- [ ] 拿到 `r2_key`：
  - [ ] 优先用 `chapter.r2_key`
  - [ ] 若空，fallback `R2Keys.chapter_pgn(chapter_id)`
- [ ] 通过 R2Client 下载：
  - [ ] `pgn_text = r2_client.download_pgn(key)`（函数名以现有 client 为准）
- [ ] 返回携带 `pgn_hash/pgn_size/last_synced_at`

### E. study/chapters 列表补充状态字段
- [ ] 在 `StudyWithChaptersResponse` 或相关 schema 中加入：
  - [ ] `pgn_status` (`ready`/`missing`)
  - [ ] `pgn_hash`, `pgn_size`, `last_synced_at`
- [ ] 计算 `pgn_status`：
  - [ ] 若 `chapter.pgn_hash` 为空或 `r2_key` 为空 -> `missing`
  - [ ] 否则 `ready`

---

## 输出物（本阶段交付）
- 新增 GET PGN API
- chapter 列表返回 PGN 状态
- 统一的读取链路（前端无需拼 R2 key）

