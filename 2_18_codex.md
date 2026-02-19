# 2/18 Codex UI & Performance Audit (Strict)

范围：`frontend/web` + `patch/`

结论先行：当前前端的主要问题不是“某个页面不好看”，而是**设计系统没有被真正执行**，并且**运行时成本管理缺失**。这会持续放大维护成本、视觉不一致和交互卡顿。

---

## 1. 设计缺陷（UI/UX）

### D1. 设计语言割裂：token 存在，但大量页面绕过 token 直接写死
- 证据：`frontend/ui/assets/variables.css:1` 定义了全局变量体系。
- 证据：`frontend/web/src/pages/BlogsPage/index.tsx:167`、`frontend/web/src/pages/SponsorshipPage/SponsorshipPage.tsx:10`、`frontend/web/src/pages/Landing/main_page.tsx:8` 大量内联写死颜色/字号/间距。
- 证据：`patch/styles/index.css:22` 起大量硬编码颜色与阴影（未复用全局 token）。
- 量化：`style={{...}}` 出现约 444 次（`frontend/web/src` 约 403，`patch` 约 41）。

影响：同一产品呈现多套视觉规则，组件无法稳定复用，后续改品牌/改主题成本极高。

提升方案：
1. 建立唯一主题层：`semantic tokens`（`--bg-surface`, `--text-primary`, `--border-muted`, `--accent`）。
2. 禁止新增内联视觉样式（仅允许动态 layout 值，如拖拽宽度）。
3. 先改高流量页：`BlogsPage`、`Landing`、`PatchStudyPage`。

---

### D2. 字体策略不一致，且存在“定义了但未加载”的字体
- 证据：`frontend/web/index.html:11` 仅加载 `Roboto`。
- 证据：`frontend/ui/assets/variables.css:17` 主字体写的是 `'Google Sans', 'Roboto'...`（Google Sans 并未在此项目加载）。
- 证据：`frontend/web/public/ui/modules/mainPage/styles/index.css:11` 又使用 `Space Grotesk`（另一套体系）。

影响：跨页面文字密度、字重、行高感知不一致，信息层级不稳定。

提升方案：
1. 限定 2 套字体角色：`brand/display` + `ui/body`。
2. 明确字体加载源并做 `font-display: swap`。
3. 全站统一字阶 token（例如 `--type-h1`, `--type-body`, `--type-caption`）。

---

### D3. 响应式覆盖严重不足，桌面固定尺寸过多
- 证据：`patch/styles/index.css:160` / `:165` 固定 `600px` 高度容器。
- 证据：`frontend/web/src/pages/analysis/analysis.css:59` / `:61` 同样固定 600px。
- 证据：`frontend/web/src/pages/Landing/LandingPage.css` 是空文件（0 行），Landing 主要靠内联固定值。
- 量化：`frontend/web/src/pages/BlogsPage`、`Landing`、`analysis`、`SponsorshipPage` 几乎无 `@media`（搜索无命中）。

影响：中小屏与大屏的可用性都不稳定；布局在高缩放/低高度视口下容易断裂。

提升方案：
1. 把“固定高度 600px”改为 `clamp()` + `min/max-height`。
2. 全站断点标准化（至少 `sm/md/lg/xl`），所有主布局组件必须有断点行为。
3. 引入容器查询（`container queries`）处理侧栏/棋盘/树面板自适应。

---

### D4. 交互语义与可访问性不足（鼠标友好，键盘与读屏弱）
- 证据：`patch/PatchStudyPage.tsx:797` 面包屑用 `onDoubleClick` 触发导航（非标准交互）。
- 证据：`patch/PatchStudyPage.tsx:793` 面包屑项是 `span`，不是按钮/链接。
- 证据：`frontend/web/src/components/navigation/SideNav.tsx:89` 等多处通过 JS `onMouseEnter/Leave` 直接改样式，缺少统一 `:focus-visible` 体系。

影响：键盘可达性差、学习成本高、无障碍评分低。

提升方案：
1. 所有可点击文本改为 `button/a`，支持 Enter/Space。
2. 为组件库统一 `focus-visible` 环。
3. 仅将“双击”作为可选增强，不应是主路径交互。

---

### D5. 视觉层级过度依赖阴影与渐变，信息结构反而变弱
- 证据：`patch/styles/index.css:22`、`:168`、`:195` 高频阴影叠加；`analysis.css:21`、`:66` 同样处理。

影响：视觉“重”，但可读层级不清晰；长期看会导致审美疲劳。

提升方案：
1. 减少阴影层级数量（建议 2 级足够）。
2. 把层级表达从“阴影”转为“间距、标题级别、分组边界”。
3. 统一表面系统（`surface/base/raised/overlay`）。

---

## 2. 性能缺陷（Runtime/Bundle/Render）

### P1. 路由未做代码分割，首包过重
- 证据：`frontend/web/src/App.tsx:30-45` 直接静态 import 多页面与 patch 模块。
- 证据：未发现 `React.lazy`/`lazy()` 用法（全仓检索无命中）。

影响：首屏下载、解析、执行成本偏高，尤其移动端更明显。

提升方案：
1. 对页面路由做 `React.lazy + Suspense`。
2. 将 `patch` 大模块（study、terminal、tagger）按路由拆包。
3. 目标：首屏 JS 体积下降 30%+。

---

### P2. 高频重渲染链仍重：分析轮询 + 流式更新 + 文本转换
- 证据：`patch/sidebar/hooks/useEngineAnalysis.ts:129` 每 2 秒轮询。
- 证据：`patch/engine/client.ts:11` 流式更新节流 200ms（最多 5 次/秒）。
- 证据：`patch/sidebar/StudySidebar.tsx:71` 每次 lines 变化都做 PV 转 SAN 与格式化。

影响：分析开启时，UI线程持续有中高负载；在低端设备上仍会拖慢交互。

提升方案：
1. `formattedLines` 引入结果缓存（key: `fen+multipv+pvHash`）。
2. 非可见 tab 停止/降采样更新。
3. 轮询改“事件驱动优先 + 退化轮询”。

---

### P3. 状态更新成本偏高：大对象 `structuredClone`
- 证据：`patch/studyContext.tsx:252`、`:310` 在 `ADD_MOVE/DELETE_MOVE` 路径直接 `structuredClone(state.tree)`。

影响：树变大后，单次操作成本线性上升，输入延迟会越来越明显。

提升方案：
1. 改成结构共享（只复制受影响分支节点）。
2. 把“树编辑”与“派生视图数据”分层，避免全树复制。
3. 增加性能预算测试（例如 10k 节点下 add/delete 延迟阈值）。

---

### P4. 重复请求用户资料，缺少统一会话缓存
- 证据：`frontend/web/src/App.tsx:359` 请求 `/user/profile`。
- 证据：`frontend/web/src/pages/BlogsPage/index.tsx:61` 再次请求同接口。

影响：多页面切换时多余网络请求，增加等待与抖动。

提升方案：
1. 引入 `Auth/User` 全局 store（React Query/SWR/Zustand 皆可）。
2. 统一 TTL 与失效策略。
3. Header/Blog 等模块改读缓存而非重复拉取。

---

### P5. 全局挂载功能组件，常驻监听增加非必要负担
- 证据：`frontend/web/src/App.tsx:451` `TerminalLauncher` 全局常驻。
- 证据：`patch/modules/terminal/frontend/TerminalLauncher.tsx:51` 常驻 `keydown` 监听。

影响：即使用户不用终端，也有额外监听和组件维护成本。

提升方案：
1. 懒加载 Terminal（首次触发时加载）。
2. 在不支持页面或移动端关闭该入口。
3. 监听器仅在 launcher 可见且功能启用时注册。

---

## 3. 优先级实施清单（建议按周执行）

### 第 1 周（高收益低风险）
1. 路由级代码分割（P1）。
2. 合并用户资料请求（P4）。
3. 统一禁用新增内联视觉样式（D1）。

### 第 2 周（体验提升）
1. Patch/Analysis 布局去固定 600px，补齐断点（D3）。
2. 面包屑/侧栏交互语义化与 focus-visible（D4）。
3. 分析面板文本转换缓存（P2）。

### 第 3 周（架构治理）
1. Tree 更新从 `structuredClone` 迁移到结构共享（P3）。
2. 建立 design tokens 2.0 并重构 Blogs/Landing/PatchStudy（D1/D2/D5）。

---

## 4. 验收指标（必须量化）

1. 首屏 JS 执行时间下降 ≥ 25%。
2. 分析开启状态下，拖拽交互帧率稳定在 55fps+（中端设备）。
3. 高流量页面内联样式数量下降 ≥ 70%。
4. Lighthouse Accessibility ≥ 90。
5. 核心布局页面（Landing/Blogs/Analysis/PatchStudy）在 390px~1920px 视口无破版。

---

## 5. 一句话结论

你现在的前端能跑，但它不是一个“可持续进化的产品 UI 系统”。先把**样式治理和渲染治理**做完，再谈精修视觉，会快很多，也稳很多。
