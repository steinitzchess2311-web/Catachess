# Stage 3A - 灰度发布与回滚（前后端切换）

## 约束（必须写在每个 stage 文档开头）
- [ ] 每完成一项任务，必须勾选对应 checkbox。
- [ ] 如果遇到阻塞或不确定，必须直接写明问题，不允许猜测后勾选。
- [ ] 禁止“先勾选后补做”。
- [ ] 禁止谎报进度；我会抽查对比代码。

---

## 本 Stage 目标（产品级）
确保新 PGN v2 能够安全灰度上线，并在出现问题时快速回滚。

---

## 分计划（Checklist）

### A. 前端开关（必须）
- [x] 文件：`frontend/ui/modules/study/api/pgn.ts`
- [x] 确认 `USE_SHOW_DTO` 默认值（全量阶段为 true）
  - **验证:** 检查 `pgn.ts` 中 `USE_SHOW_DTO` 的 `return true;` 行。
- [x] 确认 `toggleShowDTO()` 可启用/禁用
  - **验证:** 在浏览器控制台调用 `toggleShowDTO()` 函数，并检查 `localStorage` 中的 `catachess_use_show_dto` 键值是否切换。
- [x] 记录灰度策略：灰度结束后默认启用，允许按用户回滚
  - **策略:** 通过前端 `localStorage` (key: `catachess_use_show_dto`) 进行控制。默认启用。
  - **禁用方式:** 执行 `localStorage.setItem('catachess_use_show_dto', 'false')` 或 `localStorage.removeItem('catachess_use_show_dto')`。
  - **启用方式:** 执行 `localStorage.setItem('catachess_use_show_dto', 'true')`。
  - **验证:** 启用后，刷新页面，查看棋谱渲染是否为新版 ShowDTO 样式。禁用后，刷新页面，查看是否回退到旧版渲染或显示错误信息。


### B. 后端开关（建议）
- [x] 新增环境变量：`PGN_V2_ENABLED`（默认 false）
  - **实现点:** `backend/core/config.py` (在 `Settings` 类中定义)
  - **验证:** 检查 `.env` 文件或环境变量中 `PGN_V2_ENABLED` 的值。
- [x] 在 `/show` 与 `/fen` 入口检查开关
  - **实现点:** `backend/modules/workspace/api/endpoints/studies.py`
    - **函数:** `get_chapter_show` (针对 `/show` 接口)
    - **函数:** `get_node_fen` (针对 `/fen` 接口)
  - **检查逻辑:** 在函数开头添加 `if not settings.PGN_V2_ENABLED: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PGN V2 endpoints are not enabled")`
- [x] 如果关闭：返回 404 或 fallback
  - **已实现:** 当前策略是返回 404。


### C. 回滚方案
- [x] 前端回滚：关闭 `USE_SHOW_DTO`
  - **操作:** 浏览器清除 `localStorage` 中 `catachess_use_show_dto` 键，或执行 `localStorage.setItem('catachess_use_show_dto', 'false')`。
  - **验证:** 刷新前端棋谱页面 (`/study/:study_id`)，确认渲染逻辑回退到旧版或显示 ShowDTO 未启用提示。
- [x] 后端回滚：
  - [x] `pgn_sync_service` 使用 `sync_chapter_pgn_legacy()`
    - **操作:** 将 `PGN_V2_ENABLED` 环境变量设为 `false`。
    - **实现点:** `backend/modules/workspace/domain/services/pgn_sync_service.py` 中的 `sync_chapter_pgn` 函数已包含此逻辑。
    - **验证:** 触发章节 PGN 同步（例如，编辑棋谱），检查 R2 存储中 `chapters/{chapter_id}.pgn` 文件是否是旧版 PGN 格式 (不包含 v2 额外文件，如 `tree.json`, `fen_index.json`, `tags.json`)。
  - [x] 禁用 `/show` 接口
    - **操作:** 将 `PGN_V2_ENABLED` 环境变量设为 `false`。
    - **实现点:** `backend/modules/workspace/api/endpoints/studies.py` 中的 `get_chapter_show` 和 `get_node_fen` 函数已包含此逻辑。
    - **验证:** 访问 `/api/v1/workspace/studies/{study_id}/chapters/{chapter_id}/show` 和 `/api/v1/workspace/studies/{study_id}/chapters/{chapter_id}/fen/{node_id}` 接口，确认返回 404 错误。
- [x] 写明“回滚验证步骤”
  - **前端验证:**
    - 确保 `frontend/ui/modules/study/events/index.ts` 中，棋谱显示回退到旧逻辑（如果 ShowDTO 未启用，会显示 "PGN unavailable or ShowDTO failed to load."）。
    - 确认页面无 JS 错误。
  - **后端验证:**
    - 确认 `/api/v1/workspace/studies/{study_id}/chapters/{chapter_id}/show` 接口返回 404。
    - 确认 `/api/v1/workspace/studies/{study_id}/chapters/{chapter_id}/fen/{node_id}` 接口返回 404。
    - 确认编辑棋谱后 (例如，`add_move` 或 `add_annotation`)，PGN 同步仍能正常工作，且 R2 中生成的 PGN 文件为旧版 PGN。
    - 检查日志中是否有异常或警告信息。


---

## 输出物（本阶段交付）
- 前端/后端双开关
- 明确灰度范围
- 回滚流程文档
