# Catachess 设计统一整改方案（产品级）

## 角色与目标
你要求的是“首页蓝白模板”作为标准设计语言。以下方案按顶级产品设计标准输出：
- 风格关键词：简约、现代、稳定、易读、长期可维护
- 目标：把当前多套视觉风格收敛为一套系统，降低页面跳转割裂感
- 基准页面：`/`（`frontend/web/src/pages/home/HomePage.tsx` + `HomePage.css`）

---

## 0. 先定唯一设计系统（所有页面必须共用）

### 0.1 设计 Token（建议）
以蓝白体系为主，统一到 `variables.css`。

- 主色：`#2563EB`（Primary）
- 主色 Hover：`#1D4ED8`
- 页面底色：`#F5F8FC`
- 卡片底色：`#FFFFFF`
- 主文字：`#0F172A`
- 次文字：`#475569`
- 分割线：`#E2E8F0`
- 成功：`#16A34A`
- 警告：`#D97706`
- 错误：`#DC2626`

### 0.2 字体系统（统一，不混用）
当前混用了 `Inter / Space Grotesk / Roboto / Google Sans`，必须统一为一套：
- 主字体：`Inter`
- 数字/标签可用 `Inter` 同一字体，不再引入额外展示字体

### 0.3 字号与层级（统一到所有页面）
- H1：`36px / 700 / line-height 1.2`
- H2：`28px / 700 / 1.25`
- H3：`22px / 650 / 1.3`
- Section 标题：`18px / 600 / 1.4`
- 正文：`16px / 400 / 1.7`
- 辅助文案：`14px / 400 / 1.6`
- Caption/标签：`12px / 600 / 1.4 / uppercase + letter-spacing 0.04em`

### 0.4 间距、圆角、阴影
- 页面容器宽度：`max-width: 1200px`
- 卡片内边距：`24px`（移动端 `16px`）
- 区块垂直节奏：`24 / 32 / 48px`
- 圆角：卡片 `12px`，按钮 `10px`，输入框 `10px`
- 阴影：只保留两档（轻/中），杜绝每页自定义新阴影

---

## 1. 页面级整改清单（按优先级）

## P0（必须先改）

### 1. Header（`components/header/Header.css`）
问题：高度过高（100px）、导航字号偏大（20px）、信息密度低。  
修改：
- Header 高度改为 `72px`
- Logo 高度 `40-44px`
- 一级导航 `16px/600`
- 账号区 `14px/500`
- 下拉菜单项 `14px`
- 保留白底+细分割线，不使用额外花哨渐变

### 2. Footer（`components/footer/Footer.css`）
问题：紫金风格与蓝白主体系冲突，视觉噪声过高。  
修改：
- 取消紫色大渐变，改为浅色信息型 Footer：`#F8FAFC`
- 标题 `14px/600`，正文 `13px/400`
- 三列改两列（品牌+链接），移动端单列
- 删除发光动画和过强装饰，仅保留轻分割线

### 3. 全局背景风格统一
问题：About/Blogs/Translate/Sponsorship 使用米棕渐变，与首页蓝白冲突。  
修改：
- 全站统一页面底色：`#F5F8FC`
- 仅首页可保留轻微蓝调层次，其他页面统一“浅底+白卡片”

---

## P1（核心业务页统一）

### 4. About 页（`pages/aboutPage/*` + `components/navigation/SideNav.tsx`）
问题：几乎全内联样式；色彩偏棕；字号层级不稳；内容宽度与模块间距不一致。  
修改：
- 改为 CSS 模块化，去除大段 inline style
- 主标题 `H1 36px`，副标题 `18px`
- 各模块卡片统一：`background #fff`、`border 1px #E2E8F0`、`radius 12`
- 文本段落固定 `16px/1.7`
- SideNav 改为浅蓝激活态：`bg #EFF6FF / text #1D4ED8`
- 图片 hover 缩放降到 `1.03`，减少跳动

### 5. Blogs 页（`pages/BlogsPage/*`, `components/BlogHeader.tsx`）
问题：inline style 过多；色系偏棕；控件尺寸不统一；列表和详情割裂。  
修改：
- BlogHeader：标题 `24px/700`，搜索框高度 `40px`，边框统一 `#CBD5E1`
- Sidebar 宽度固定 `260px`（收起 64px），按钮统一 `14px/500`
- 文章卡片：标题 `20px`，摘要 `15px`，meta `13px`
- 详情页正文行宽控制在 `72ch`
- 交互色全部收敛到 Primary 蓝系

### 6. Translate 页（`pages/translate/*`）
问题：整体是另一套 Google 风格，字号偏大（标题 42px），与站内不一致。  
修改：
- 标题改 `32px`，副标题 `16px`
- 卡片宽度 `max-width: 760px`，内边距 `24px`
- 上传区高度减少 15%-20%，避免过于“工具站”感
- 进度条、按钮、输入框全部使用统一 token

### 7. Sponsorship 页（`pages/SponsorshipPage/*`）
问题：视觉语言沿用旧米棕主题，信息结构弱。  
修改：
- 标题层级：`H1 36`、副标题 `16`
- 资助内容改为“卡片列表”（每条卡片 `16px` 正文）
- 删除棕色圆点数字，改为蓝色编号徽章
- 增加“资金用途透明度”信息块（结构化信任）

### 8. Analysis 页（`pages/analysis/analysis.css`）
问题：与首页有一定一致性，但容器高度写死 600px，响应式风险高。  
修改：
- `analysis-layout` 高度改为：`min(72vh, 760px)`
- 标题 `28px` -> `24px`，按钮高度统一 `40px`
- 左右栏边线对比度降低，减少“割裂线”感
- 移动端：改单列（棋盘在上，面板下移）

---

## P2（次级页面与补齐）

### 9. Players / Profile / Games（`patch/modules/*`）
问题：深色 Hero 风格与首页蓝白冲突。  
修改：
- Hero 改浅蓝渐变（不是黑蓝）
- 大标题保留，但降对比度，统一到主站语气
- 卡片与按钮直接复用全局 token
- 保留功能布局，不动交互逻辑

### 10. Account/Edit Profile（`frontend/web/AccountPage.tsx`）
问题：纯临时内联表单，产品感弱。  
修改：
- 建立标准表单页模板（标题区 + 表单卡片 + 固定操作区）
- Label `14px/600`，Input `16px`，按钮 `40px` 高
- 成功/失败提示标准化为 toast 或 inline status

### 11. Admin 页面（`pages/AdminPanel/RoleManagement.tsx`）
问题：开发态样式，缺少统一表格规范。  
修改：
- 表格头 `13px/700 uppercase`
- 行高 `48px`
- 筛选区改固定高度工具条
- 所有操作按钮统一主次按钮体系

---

## 2. 代码层面落地要求（不改逻辑，只改样式结构）
- 禁止继续新增大段 inline style（尤其 Blogs/About）
- 每个页面建立独立 `.css` 或 `.module.css`
- 颜色/字号/圆角/阴影全部走 token 变量
- 动效最多两类：`fade/slide`，时长 `150-220ms`
- 先保证桌面端，再补移动端断点（`1024 / 768 / 480`）

---

## 3. 推荐执行顺序（4 个阶段）
1. 全局层：Header + Footer + Token 收敛
2. 内容页：About / Blogs / Translate / Sponsorship
3. 功能页：Analysis / Players / Profile / Games
4. 管理页：Account / Admin + 全站视觉 QA

---

## 4. 结果标准（验收）
满足以下 6 条即通过：
- 任意两个页面来回切换，无“换了一个网站”的割裂感
- 字体只剩一套，字号层级稳定
- 所有按钮/输入/卡片边角和阴影一致
- 蓝白为主，米棕/紫金/深色主题不再主导
- 移动端无横向滚动，主要页面可完整使用
- 新页面可直接复用现有样式 token，而不是重新造一套
