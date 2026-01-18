# Stage 2E - 前端棋谱展示 UI 规范（主线/变化/注释）

## 约束（必须写在每个 stage 文档开头）
- [ ] 每完成一项任务，必须勾选对应 checkbox。
- [ ] 如果遇到阻塞或不确定，必须直接写明问题，不允许猜测后勾选。
- [ ] 禁止“先勾选后补做”。
- [ ] 禁止谎报进度；我会抽查对比代码。

---

## 本 Stage 目标（产品级）
让“棋谱展示栏”在前端完整支持：主线、变化、注释，并且可点击跳局面。
前端同学不需要了解后端或 PGN 语法，只需遵循此规范即可实现。

---

## 输入数据规范（ShowDTO）

### 1) 必须请求的接口
- [ ] `GET /api/v1/workspace/studies/{study_id}/chapters/{chapter_id}/show`

### 2) 必须消费的字段
- [ ] `headers`: `[{"k":"Event","v":"..."}, ...]`
- [ ] `root_fen`: 字符串
- [ ] `result`: `"1-0" | "0-1" | "1/2-1/2" | "*"`
- [ ] `nodes`: `node_id -> node`
- [ ] `render`: token 流

### 3) render token 结构
- [ ] move token：`{"t":"move","node":"n1","label":"1.","san":"Nf3"}`
- [ ] comment token：`{"t":"comment","node":"n1","text":"..."}`
- [ ] variation start：`{"t":"variation_start","from":"n1"}`
- [ ] variation end：`{"t":"variation_end"}`

---

## UI 展示规范（必须按此实现）

### A. 主线展示
- [ ] 主线按 token 顺序横向排版：
  - 例：`1. Nf3 d5 2. g3 Nf6 ...`
- [ ] `label` 出现时显示回合号；为空则仅显示 `san`
- [ ] 白方与黑方步可同一行，也可折行（优先同一行）

### B. 变化展示（variation）
- [ ] 遇到 `variation_start`，开始渲染“变化块”
- [ ] 变化块样式：
  - [ ] 可缩进一层或用括号包裹
  - [ ] 起始处显示 `(`
  - [ ] 结束处显示 `)`
- [ ] 变化块内部继续按 token 顺序渲染
- [ ] 变化块可嵌套（最多 5 层）

### C. 注释展示（comment）
- [ ] 注释默认折叠：
  - [ ] 显示前 120 字或首句（遇到 `。` 结束）
  - [ ] 提供“展开/收起”按钮
- [ ] 展开后显示完整注释文本
- [ ] 注释样式需弱化（灰色/斜体/小字号）

### D. 点击与交互
- [ ] 点击 move token：
  - [ ] 从 `nodes[node_id].fen` 取 FEN
  - [ ] 棋盘跳转到该 FEN
- [ ] hover move token：
  - [ ] 临时预览该 FEN
  - [ ] 鼠标离开恢复原局面

### E. 结果与起始局面
- [ ] 起始局面用 `root_fen`
- [ ] 显示 `result` 在棋谱末尾

---

## 最小实现顺序（避免阻塞）

### Step 1: 渲染主线
- [ ] 仅处理 move token，忽略 variation/comment

### Step 2: 渲染变化
- [ ] 支持 variation_start / variation_end
- [ ] 用括号/缩进块表现

### Step 3: 渲染注释
- [ ] 加折叠逻辑

### Step 4: 点击跳转
- [ ] 点击 move -> fen
- [ ] hover 预览

---

## 输出物（本阶段交付）
- 前端棋谱展示栏（支持主线/变化/注释）
- 可点击跳 FEN
- 注释折叠/展开

