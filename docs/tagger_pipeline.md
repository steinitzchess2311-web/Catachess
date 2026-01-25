# Tagger Pipeline 产品级方案（中文版）

负责人：产品 + 工程
目标：做一个可上线的“棋手风格分析”系统（用户上传 PGN → 统计 tag）
受众：不读代码也能落地的团队成员

---

## 0. 目标与边界

### 目标
- 用户创建“棋手档案（Player Profile）”。
- 上传 PGN 后计算该棋手的 tag 统计（白方、黑方、总计）。
- 支持增量上传：不需要重新上传老 PGN，也不重复计数。
- 存储原始 PGN 以便未来重算、审计与导出。
- 前端体验清晰、可追踪进度。

### 边界（v1 不做）
- 不做实时对局分析。
- 不抓取外部公开库。
- 只分析主线（不分析变体）。

---

## 1. Pipeline 逻辑（清晰可执行）

### 1.1 总流程
1) 用户新建棋手档案（名称 + 可选别名）。
2) 用户上传一个或多个 PGN。
3) 后端解析 PGN，识别该棋手是白方还是黑方。
4) 对该棋手走的每一步进行 tag 分析。
5) 统计结果累加到白/黑/总三套统计。
6) 存储结果并返回可视化数据。

### 1.2 细节流程（逐盘处理）
- 输入：PGN 文件 + 用户输入棋手名。
- 名称处理：
  - 规范化：去标点/空格/大小写/重音。
  - 匹配优先级：aliases > display_name > 模糊匹配（PGN White/Black）。
  - 模糊匹配 PGN headers 里的 White/Black。
  - 若匹配不唯一 → 弹出确认选择，选择结果写入别名。
- 走子筛选：
  - 解析 PGN 为主线步序列。
  - 用 `board.turn` 判断当前走子方，只有目标棋手走的步才统计。
- Tagger：
  - 用 FEN + 实际走子调用 tagger。
  - 记录 tag 命中。
- 统计：
  - 白方统计、黑方统计、总统计同步累加。

### 1.3 统计口径（必须统一）
- 百分比分母 = 该棋手走子总步数。\n- 白/黑统计各自独立分母，总统计为两者之和。\n- 保证白/黑/总三套统计口径一致、可比较。

---

## 2. 调度与模块说明（后端）

### 2.1 必备模块
- PGN Parser：读取 PGN，输出每盘 headers 与主线走子。
- Player Matcher：模糊匹配棋手名，支持人工确认。
- Tagger Runner：调用 tagger（引擎走 `sf.catachess.com`）。
- Stats Aggregator：白/黑/总三套计数与百分比。
- 存储模块：
  - R2：存原始 PGN。
  - Postgres：存档案、索引、统计、去重。

### 2.2 调度策略
- 小文件：同步处理（请求内完成）。
- 大文件：异步任务（建议 worker + 队列）。
- 需要有：
  - 进度/状态查询
  - 失败可重试
  - 保证不重复计入

### 2.3 去重与增量
- 每盘棋生成 `game_hash`（规范化后的 headers + 主线走子）。\n- `game_hash` 与 player_id 绑定存表。\n- 再次上传时跳过已处理的 game_hash。\n- 规范化规则：\n  - headers 仅保留识别对局所需字段（White/Black/Date/Event/Result），忽略站点/时间戳等不稳定字段。\n  - 主线走子统一为标准 UCI（或 SAN）后再 hash。

### 2.4 失败处理策略（明确规则）
- 单盘失败不影响整次上传。\n- 失败盘记录 headers + 原因，前端可查看“失败清单”。\n- 上传整体状态可为 completed_with_errors。

---

## 3. 存储设计

### 3.1 R2（原始 PGN）
- 新建 bucket：`catachess-pgn`
- 路径规范：
  - `players/{player_id}/{upload_id}/raw.pgn`
  - `players/{player_id}/{upload_id}/meta.json`

### 3.2 Postgres（建议表）

**1) player_profiles**
- id (uuid)
- display_name
- normalized_name
- aliases (text[])
- created_at / updated_at

**2) pgn_uploads**
- id (uuid)
- player_id
- r2_key_raw
- checksum
- status (pending/processing/done/failed/completed_with_errors)
- created_at / updated_at

**3) pgn_games**
- id (uuid)
- player_id
- upload_id
- game_hash (unique per player)
- white_name / black_name
- player_color (white/black)
- game_result
- move_count

**4) tag_stats**
- player_id
- scope (white/black/total)
- tag_name
- tag_count
- total_positions（该棋手走子总步数）
- updated_at

**5) tag_runs（审计可选）**
- id
- player_id
- engine_version
- depth / multipv
- processed_positions
- started_at / finished_at

---

## 4. 文件架构（细到目录级）

### 4.1 Backend

**backend/core/tagger/**
- 保留基础 tagger 单点分析能力

**backend/modules/tagger/**
- api.py：对外 API
- service.py：解析/匹配/去重/统计的调度核心
- storage/
  - r2_client.py
  - postgres_repo.py
- pipeline/
  - pgn_parser.py
  - player_matcher.py
  - tagger_runner.py
  - stats_aggregator.py
  - dedupe.py
- schemas/
  - request/response DTO
- jobs/（可选）
  - worker.py / queue.py
- docs/
  - pipeline_notes.md（内部运行说明）

### 4.2 Frontend（Patch）

**patch/modules/tagger/**
- pages/
  - PlayersIndex.tsx（玩家列表 + 新建）
  - PlayerDetail.tsx（上传 + 统计）
- components/
  - PlayerCard.tsx
  - UploadPanel.tsx
  - StatsTable.tsx
  - ProgressBar.tsx
  - ConfirmMatchModal.tsx
- api/
  - taggerApi.ts
- styles/
  - tagger.css

路由：
- `/players` → PlayersIndex
- `/players/:id` → PlayerDetail

---

## 5. 前端产品设计（明确可交付）

### 5.1 导航
- Header 在 About Us 左侧新增 “Players”。
- 路由：`https://catachess.com/players`

### 5.2 Players 列表页
- 风格与主页一致。
- 顶部标题：Players
- CTA：New Player
- 卡片信息：棋手名 / 已分析位置数 / 最近更新时间

### 5.3 Player 详情页
- 顶部：
  - 棋手名 + 别名
  - 状态（Idle / Processing / Error / CompletedWithErrors）
- 上传区：
  - 拖拽上传 + Import PGN 按钮
  - 进度条 + 解析日志
- 输出区：
  - 三个 Tab：Total / White / Black
  - 表格：tag + count + percentage
  - Export 按钮（CSV / JSON）

### 5.4 人工确认
- 模糊匹配不唯一时弹窗选择：
  - 显示候选 White/Black 名称
  - 选择后写入别名列表

---

## 6. 引擎与 Tagger 规则

- 引擎：`https://sf.catachess.com/engine`
- 深度与 multipv 可配置
- 每步严格检查合法走法

---

## 7. 可运维要求

- 进度可查询（上传状态、已处理盘数）
- 可重试（引擎 503 时重试）
- 去重保证（game_hash）
- 支持未来“重算”能力

---

## 8. API 草案（后端）

- POST `/api/tagger/players`
- GET `/api/tagger/players`
- GET `/api/tagger/players/:id`
- POST `/api/tagger/players/:id/uploads`
- GET `/api/tagger/players/:id/stats`
- GET `/api/tagger/players/:id/exports?format=csv|json`

---

## 9. 开发清单（交付标准）

- [ ] R2 bucket 创建并配置
- [ ] Postgres 表结构落地
- [ ] 模糊匹配 + 人工确认
- [ ] 去重逻辑
- [ ] Pipeline + 统计落地
- [ ] 前端 Players 页面
- [ ] 导出能力
- [ ] 运行说明与回归测试

## 10. 测试与验收

### 10.1 基准测试数据
- 使用 `tagger/player_pgn/louyiping` 下的 PGN 文件作为默认测试集。
