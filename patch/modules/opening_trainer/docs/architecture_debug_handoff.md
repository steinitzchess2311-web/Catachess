# Opening Trainer 前后端协同架构与 Debug 交接文档

## 1. 文档目标

这份文档给没有看过代码的同事使用，帮助快速理解：
- Opening Trainer 前端和后端怎么配合。
- 关键代码分别在哪些文件。
- 一次训练请求从点击到落库的完整链路。
- 当前 404 问题最可能的来源和排查顺序。

---

## 2. 总体架构（一句话）

Opening Trainer 是“前端状态机 + 后端无状态校验/推进”的架构：
- 前端负责 UI、会话状态持有、调用 API。
- 后端每次根据 `study + mode + color + session` 重新计算可训练树并校验。
- 进度持久化只存 `(user_id, from_fen, move_san, color)` 粒度，不绑定 study/chapter。

---

## 3. 代码地图（先看这个）

## 3.1 前端（入口、页面、网络层）

- 路由注册（Opening Trainer 页面挂载）
  - `frontend/web/src/App.tsx`
  - 关键位置：
    - lazy import: 第 60 行
    - route: 第 612-614、628-629 行

- Study 页入口（弹窗选择 Position / Opening Trainer）
  - `patch/PatchStudyPage.tsx`
  - 关键位置：
    - 模态状态 `showTrainerLauncher`: 第 75 行
    - 打开模态 + 跳转 opening trainer: 第 543-552 行

- 入口弹窗组件
  - `patch/modules/opening_trainer/TrainerLauncherModal.tsx`

- Opening Trainer 主页面（最核心）
  - `frontend/web/src/pages/openingTrainer/OpeningTrainerPage.tsx`
  - 关键逻辑：
    - 错误格式化 `readApiError`: 第 194 行
    - catalog/detail 请求防竞态序列号：第 245-246 行
    - catalog 就绪门控 `isCatalogReady`: 第 253 行
    - `refreshUnits`（资格+units+progress 拉取）：第 255 行
    - detail 请求（含 `encodeURIComponent`、404 回退）：第 336 行附近
    - `startRun`（启动训练，含 scope 门控）：第 357 行
    - `submitAnswer`（提交答案）：第 414 行

- API 客户端（所有页面共用）
  - `frontend/ui/assets/api.ts`
  - 关键逻辑：
    - `detailToMessage`（把对象错误变成可读字符串）: 第 27 行
    - `request`（附 token、抛错、状态码透传）: 第 57 行

## 3.2 后端（路由、服务、Schema、DB）

- 在主应用挂载 Opening Trainer Router
  - `backend/main.py`
  - `app.include_router(opening_trainer_router)`: 第 606 行

- API 路由层（HTTP 契约与依赖注入）
  - `backend/modules/opening_trainer/api/router.py`
  - 路由前缀：第 56 行 `/api/v1/opening-trainer`
  - 核心端点：
    - eligibility: 第 322 行
    - units: 第 345 行
    - unit detail: 第 375 行
    - train start: 第 417 行
    - train answer: 第 489 行
    - progress GET: 第 613 行
    - progress POST: 第 668 行

- 训练树/分拆算法（业务核心）
  - `backend/modules/opening_trainer/service.py`
  - 核心函数：
    - `normalize_fen_key`: 第 32 行
    - `build_eligibility_summary`: 第 94 行
    - `_build_leaf_node`: 第 247 行
    - `_build_unit_tree`: 第 329 行
    - `build_unit_catalog`: 第 390 行
    - `get_leaf_unit`: 第 502 行
    - `advance_until_prompt`: 第 539 行

- 数据契约（请求/响应模型）
  - `backend/modules/opening_trainer/schemas.py`

- Opening Trainer 独立 DB 连接（读取 `OPENING_TRAINER_URL`）
  - `backend/modules/opening_trainer/db.py`
  - 关键：第 16-18 行

---

## 4. 前后端协同链路（按真实调用顺序）

## 4.1 进入页面后的初始化

1. 前端读取 URL 中 `studyId`。
2. 调用 `GET /studies/{study_id}/eligibility`。
3. 若 `eligible=false`：
   - 前端只展示 “Study Not Ready” 与原因。
   - 不再请求 `/units`。
4. 若 `eligible=true`：
   - 调用 `GET /studies/{study_id}/units?mode=&color=`。
   - 取 `leaf_units`，选中首个 unit。
   - 收集 `required_fens` 调 `GET /progress`，渲染 mastery。
5. 选中 unit 后再调 `GET /studies/{study_id}/units/{unit_id}?mode=&color=` 获取 line detail。

## 4.2 启动训练

1. 点击 `Start Session`。
2. 前端调 `POST /studies/{study_id}/train/start`，body 含：
   - `mode`
   - `color`
   - `training_mode`
   - `unit_id`
3. 后端从 catalog 重新定位 unit，随机选 line，返回：
   - `session`
   - `prompt`
   - `auto_moves`
   - `finished`
4. 前端据此更新棋盘和输入区。

## 4.3 提交答案

1. 前端调 `POST /studies/{study_id}/train/answer`，body 含：
   - `session`
   - `user_move_san`
2. 后端校验 SAN，对 quiz 模式写入 `opening_trainer_moves`。
3. 返回新 `session + prompt + progress + auto_moves`。
4. 前端更新 streak/correct/wrong/mastery UI。

---

## 5. 数据与状态模型（调试时最常看）

## 5.1 关键主键

- Study 级：`study_id`
- Unit 级：`unit_id`（后端根据内容哈希生成，如 `ot_unit_xxx`）
- 步级进度：`(user_id, from_fen, move_san, color)`

## 5.2 为什么 unit 会“看起来存在但 404”

常见场景不是后端真的没有，而是“前端拿了旧 unit_id 请求新 catalog”：
- 用户快速切换 `mode/color`。
- 旧请求返回顺序晚于新请求（竞态）。
- detail/start 请求引用了上一版 catalog 的 unit_id。

所以最近修复重点都在“请求时序门控 + scope 一致性校验 + 404 回退”。

---

## 6. 最近已做的稳定性修复（便于同事判断是否已包含）

前端相关提交（按时间倒序）：
- `ca538ab`：`start` 只能在 active catalog scope 就绪时触发。
- `c29718f`：加请求序列门控；detail 路径参数 URL 编码。
- `164fec3`：避免 catalog 切换时旧 `unit_id` 导致 404。
- `a985843`：ineligible 不再请求 units；修复 `[object Object]` 错误展示。
- `79ea8d2` / `af643c6`：Opening Trainer 页面与入口 UI 主体实现。

后端相关提交：
- `87bd8d1`：runtime API（start/answer）与契约完善。
- `23ccf25`：eligibility + unit splitting API。
- `3a4b5c8`：progress 与建表基础。
- `702b6fd`：移除 main.py 临时建表脚本（已按要求清理）。

---

## 7. 404 问题排查清单（给 Debug 同事）

按顺序执行，不要跳步。

1. 浏览器 Network 里确认是哪条 404：
   - `/eligibility`
   - `/units`
   - `/units/{unit_id}`
   - `/train/start`
   - `/train/answer`

2. 抓这四个字段：
   - `study_id`
   - `mode`
   - `color`
   - `unit_id`（若该端点有）

3. 若是 `/units/{unit_id}` 或 `/train/start` 404：
   - 先看同一时刻的 `/units` 响应里是否包含这个 `unit_id`。
   - 若不包含，基本就是“旧 unit_id 请求新 catalog”。

4. 后端日志里看 router 抛错 detail：
   - `Unit not found: ...` → catalog/unit 不一致
   - `Node ... is not a study` → 路由 id 不是 study
   - `Node not found` → study_id 本身失效或权限问题

5. 若问题只在线上出现，重点看：
   - 前端版本是否是最新 commit（`ca538ab` 之后）
   - CDN/浏览器是否缓存老 JS
   - Railway 多实例滚动时是否出现旧新版本混跑

---

## 8. 关于你看到的 PostgreSQL 日志

`could not receive data from client: Connection reset by peer`

这通常是客户端或代理先断开 TCP，不是 Opening Trainer 表结构错误。常见来源：
- 页面刷新或请求取消
- 进程重启
- 代理/连接池 idle timeout

只有当它伴随大量 5xx 或事务失败时，才算核心故障线索。

---

## 9. 关于“是否要把所有前端都搬到 patch”

结论：
- 可以搬，能提升代码集中度和团队维护体验。
- 但不会直接解决当前 404。

当前 404 的关键是“状态/请求时序一致性”，不是目录结构本身。

---

## 10. 你同事接手时推荐先读顺序

1. `frontend/web/src/pages/openingTrainer/OpeningTrainerPage.tsx`
2. `backend/modules/opening_trainer/api/router.py`
3. `backend/modules/opening_trainer/service.py`
4. `frontend/ui/assets/api.ts`
5. `patch/PatchStudyPage.tsx` + `TrainerLauncherModal.tsx`

按这 5 个文件读完，基本可以完整掌握这个模块。
