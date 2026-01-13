# 前端重构计划审查报告

**审核日期:** Jan 12, 2026 8:02 PM
**审核者:** Codex
**计划版本:** Final Approved Version (2026-01-12)
**审核结果:** ⚠️ **有条件批准（需补充 Stage 0）**

---

## 执行摘要

技术规范写得很漂亮：Material 3 设计系统专业，Vertical Slice 架构清晰，Protocol 文档严谨。**但你们漏了最关键的一步：删除遗留代码的步骤。**

**核心问题：你们只写了"怎么建新房子"，没写"怎么拆旧房子"。**

---

## 一、优点（值得表扬的）

### 1. 设计系统专业 ⭐⭐⭐⭐⭐
- Material 3 色彩、字体、圆角、间距、阴影规范完整
- CSS Variables 强制使用策略正确
- 这是 Google 级别的设计规范

### 2. 架构思路清晰 ⭐⭐⭐⭐⭐
- Vertical Slice 架构，`layout/events/styles/` 三层分离
- 禁止 HTML 字符串、inline scripts、魔法数字
- 这是现代前端最佳实践

### 3. Backend Blocker 识别精准 ⭐⭐⭐⭐⭐
- 明确指出 `versions` 和 `presence` 路由未挂载
- 给出了具体文件路径和修复代码
- 可执行性强

### 4. Protocol 文档严谨 ⭐⭐⭐⭐⭐
- Frontend-Backend 分离原则明确
- The Triad 边界规定清晰
- 应该打印出来贴墙上

---

## 二、致命缺陷（必须修复）

### 🔥 问题 1：缺少 Stage 0（遗产清理）

**你们打算删除重写这些模块，但计划里没写删除步骤：**

| 模块 | 实际情况 | 应该怎么处理 | 计划怎么说的 |
|-----|---------|------------|------------|
| `workspace/` | 45 个 TS 文件，结构混乱 | 🗑️ **删除重写** | ❌ 只说"创建"，没说删 |
| `login/` | 旧实现，不符合新架构 | 🗑️ **删除重写** | ❌ 只说"创建"，没说删 |
| `signup/` | 4 个 TS 文件 + modules 子目录 | 🗑️ **删除重写** | ❌ 只说"创建"，没说删 |
| `games/` | 在 Hetzner 云服务器上 | 🔒 **保留但不上线** | ❌ 说"删除"，但不该删 |
| `core/` | 基础设施（drag, focus, resize） | ✅ **保留使用** | ✅ 正确 |
| `chessboard/` | 核心棋盘逻辑 | ✅ **保留使用** | ✅ 正确 |

**后果：**
- 开发者不知道要先删 workspace/login/signup
- 可能误删 core/ 或 chessboard/
- 新旧代码冲突
- games/ 被错误删除

---

### 🔥 问题 2：games/ 的处理错误

**计划说（stage1）：**
> Delete Directory: `frontend/ui/modules/games/`

**实际要求：**
- games/ 在 Hetzner 云服务器上运行
- 暂不上线，但**不删除**
- 应该归档（加 README 说明），不是删除

**这个错了。**

---

### 🔥 问题 3：没有依赖检查和备份步骤

删除 workspace/login/signup 前：
- ❌ 没检查是否有其他代码依赖它们
- ❌ 没有备份策略
- ❌ 没有回滚方案

**万一删错了怎么办？**

---

## 三、必须补充的内容（P0 - 今晚完成）

### 1. 创建 `stage0_legacy_cleanup.md`

必须包含：

```markdown
# Stage 0: Legacy Code Cleanup

## A. 保留清单（Do NOT Delete）
- ✅ `frontend/ui/core/` - 基础设施，新系统会用
- ✅ `frontend/ui/modules/chessboard/` - 核心功能，已模块化

## B. 归档清单（Archive, Do Not Use）
- 🔒 `frontend/ui/modules/games/` - Hetzner 服务器，保留但不上线
  - 操作：创建 README.md 说明归档状态
  - 禁止：删除、集成到新系统

## C. 删除清单（Delete and Rewrite）
- 🗑️ `frontend/ui/modules/workspace/` - 45 文件，结构混乱
- 🗑️ `frontend/ui/modules/login/` - 旧架构，不符合标准
- 🗑️ `frontend/ui/modules/signup/` - 旧架构，不符合标准

## D. 操作步骤

1. **创建备份：**
   ```bash
   git checkout -b backup-legacy-$(date +%Y%m%d)
   git tag legacy-backup-$(date +%Y%m%d)
   git checkout main
   ```

2. **归档 games/：**
   ```bash
   echo "# ARCHIVED - Do Not Use\nRunning on Hetzner server. Do NOT delete." > frontend/ui/modules/games/README.md
   ```

3. **检查依赖并删除：**
   ```bash
   # 检查 workspace 依赖
   grep -r "from.*workspace" frontend/ui --exclude-dir=workspace
   grep -r "import.*workspace" frontend/ui --exclude-dir=workspace

   # 如果没有输出，安全删除
   rm -rf frontend/ui/modules/workspace
   rm -rf frontend/ui/modules/login
   rm -rf frontend/ui/modules/signup
   ```

4. **验证：**
   ```bash
   # 应该存在
   ls frontend/ui/core
   ls frontend/ui/modules/chessboard
   ls frontend/ui/modules/games/README.md

   # 不应该存在
   ls frontend/ui/modules/workspace 2>&1 | grep "No such file"
   ls frontend/ui/modules/login 2>&1 | grep "No such file"
   ls frontend/ui/modules/signup 2>&1 | grep "No such file"
   ```

5. **提交：**
   ```bash
   git add -A
   git commit -m "chore: Stage 0 - cleanup legacy modules"
   git tag stage0-complete
   ```
```

---

### 2. 修订 `stage1_setup_and_blockers.md`

**删除这一行：**
```markdown
- [ ] **Delete Directory**: `frontend/ui/modules/games/`.
```

**改成：**
```markdown
## 2. Verify Stage 0 Completion (遗产清理验证)

在开始 Stage 1 之前，必须确认 Stage 0 已完成：

- [ ] **Verify Protected Modules**:
    - [ ] `frontend/ui/core/` 存在
    - [ ] `frontend/ui/modules/chessboard/` 存在

- [ ] **Verify Archived Module**:
    - [ ] `frontend/ui/modules/games/` 存在
    - [ ] `frontend/ui/modules/games/README.md` 存在并包含 "ARCHIVED"

- [ ] **Verify Deleted Modules**:
    - [ ] `frontend/ui/modules/workspace/` 不存在
    - [ ] `frontend/ui/modules/login/` 不存在
    - [ ] `frontend/ui/modules/signup/` 不存在

- [ ] **Verify Git Tag**:
    - [ ] `git tag` 显示 `stage0-complete`
```

---

### 3. 在 `COMPLETE_PLAN.md` 添加 Section 0.2

```markdown
## 0.2 🛡️ 保留的遗产（Protected Modules）

以下模块**已符合架构标准**，将被新系统使用，**严禁删除**：

### `ui/core/` - 窗口管理基础设施
- **功能：** Drag（拖拽）、Focus（焦点）、Resize（调整大小）
- **使用场景：** "New Folder" 弹窗、Study 面板拖拽
- **保留理由：** 基础设施，代码质量好，不需要重写
- **警告：** 删除此模块会导致所有弹窗功能失效

### `ui/modules/chessboard/` - 核心棋盘逻辑
- **功能：** 棋盘渲染、移动验证、PGN 解析
- **使用场景：** Study 模块的棋盘显示
- **保留理由：** 核心功能，已模块化，稳定可靠
- **警告：** 删除此模块会导致整个应用无法使用
```

---

## 四、建议补充的内容（P1 - 明天完成）

### 4. 创建 `ROLLBACK.md`

```markdown
# 回滚策略

## 每个 Stage 完成后打 tag
```bash
git tag -a stage0-complete -m "Stage 0: Legacy Cleanup"
git tag -a stage1-complete -m "Stage 1: Setup & Blockers"
git tag -a stage2-complete -m "Stage 2: Auth"
git tag -a stage3-complete -m "Stage 3: Workspace"
git tag -a stage4-complete -m "Stage 4: Study & Discussion"
```

## 回滚命令
如果 Stage 2 出问题：
```bash
git reset --hard stage1-complete
git clean -fd
```

## 分支策略（推荐）
每个 Stage 用独立分支：
```bash
git checkout -b stage1-setup
# ... 完成 Stage 1 ...
git checkout main
git merge stage1-setup --no-ff
git tag stage1-complete
```
```

---

### 5. 创建 `EFFORT_ESTIMATION.md`

```markdown
# 工作量评估

| Stage | 任务 | 预估时间 | 风险 |
|-------|-----|---------|------|
| Stage 0 | Legacy Cleanup | 1-2 小时 | 低 |
| Stage 1 | Setup & Blockers | 4-6 小时 | 低 |
| Stage 2 | Auth (Login + Signup) | 12-16 小时 | 中 |
| Stage 3 | Workspace | 20-30 小时 | 高 |
| Stage 4 | Study + Discussion | 30-40 小时 | 高 |
| **总计** | | **67-94 小时** | |

**结论：** 约 2-2.5 周，1 人全职工作
```

---

## 五、整体评分

| 维度 | 评分 | 说明 |
|-----|------|------|
| **技术规范** | ⭐⭐⭐⭐⭐ 5/5 | Material 3 + Vertical Slice 无可挑剔 |
| **可执行性** | ⭐⭐ 2/5 | 缺 Stage 0，开发者不知道先删什么 |
| **完整性** | ⭐⭐ 2/5 | 缺删除策略、归档策略 |
| **风险意识** | ⭐⭐ 2/5 | 没备份、没回滚、没依赖检查 |
| **文档质量** | ⭐⭐⭐⭐⭐ 5/5 | 清晰专业，Protocol 应成为团队标准 |

**总分：3.2 / 5**

**评价：及格，但有致命遗漏。技术能力很强，项目管理需要改进。**

---

## 六、最终决定

### ✅ 有条件批准（Conditional Approval）

**批准内容：**
- ✅ Stage 1-4 的技术规范（不需要修改）
- ✅ 设计系统和架构原则（非常优秀）
- ✅ Backend Blocker 修复方案（准确无误）

**批准条件：**
- ⚠️ **必须先补充 Stage 0**（今晚完成）
- ⚠️ **必须修改 stage1**（删除 "Delete games/" 那行）
- ⚠️ **必须添加 Section 0.2**（说明保留策略）

**补充完成后，可以立即开始执行。**

---

## 七、执行要求

### 必须遵守的规则

1. **Stage 0 必须第一个执行**
   - 不清理遗产，后面的 Stage 无法开始

2. **每个 Stage 完成后打 git tag**
   - 格式：`stage0-complete`, `stage1-complete`, ...
   - 方便回滚

3. **禁止跳 Stage**
   - Stage 依赖关系清晰，必须按顺序执行

4. **禁止删除 core/ 和 chessboard/**
   - 这两个模块是保留的，删了就完蛋

5. **禁止删除 games/**
   - 只能归档（加 README），不能删

---

## 八、给老板的建议

### 如果你批准这个计划

1. **今晚让团队补充 P0 内容**（Stage 0 + 修改 stage1 + 添加 Section 0.2）
2. **明天早上审查补充内容**
3. **审查通过后，批准执行**
4. **要求每个 Stage 完成后汇报**

### 批准后的监督重点

1. **Stage 0 执行时**：确认 games/ 没被删，workspace/login/signup 被删了
2. **Stage 1 执行时**：确认 Backend Router 修复了，assets/ 创建了
3. **Stage 2-4 执行时**：确认代码符合 Vertical Slice（layout/events/styles 三层）

### 我的评价

**这个团队技术能力很强，但项目管理有疏漏。**

- ✅ 设计规范写得比我见过的大部分团队都好
- ✅ 架构思路清晰，Protocol 文档严谨
- ❌ 但忘记了写"清理遗产"的步骤
- ❌ games/ 的处理方式搞错了

**总结：会干活，但粗心。补上 Stage 0 就完美了。**

---

## 九、需要补充的文档清单

### 🔴 P0 - 今晚必须完成（否则不批准）

```bash
frontend/docs/implementation/stage0_legacy_cleanup.md     # 新建
frontend/docs/overview/COMPLETE_PLAN.md                    # 修改：添加 Section 0.2
frontend/docs/implementation/stage1_setup_and_blockers.md  # 修改：改 games/ 处理
```

### 🟠 P1 - 明天完成（强烈建议）

```bash
frontend/docs/implementation/ROLLBACK.md           # 新建
frontend/docs/implementation/EFFORT_ESTIMATION.md  # 新建
```

### 🟡 P2 - 有时间再做（可选）

```bash
frontend/docs/implementation/PERFORMANCE.md        # 新建
frontend/docs/implementation/API_ERROR_HANDLING.md # 新建
frontend/docs/implementation/DEPENDENCY_MAP.md     # 新建
```

---

## 十、下次审查

**时间：** Stage 0 补充完成后（预计 Jan 13, 2026）

**审查内容：**
- Stage 0 文档是否完整（保留/归档/删除清单）
- stage1 是否修改了 games/ 的处理方式
- Section 0.2 是否添加了保留策略说明

**如果审查通过，立即批准执行。**

---

**签名：** Codex
**日期：** Jan 12, 2026 8:02 PM
**审查时长：** 2.5 小时
**态度：** 严厉但公正 —— 你们做得不错，补上遗漏就完美

---

## 附录：Stage 0 快速参考

为了方便执行，这里是 Stage 0 的核心命令：

```bash
# 1. 备份
git checkout -b backup-legacy-$(date +%Y%m%d)
git tag legacy-backup-$(date +%Y%m%d)
git checkout main

# 2. 归档 games
cat > frontend/ui/modules/games/README.md << 'EOF'
# ARCHIVED MODULE - DO NOT USE
Running on Hetzner cloud server.
Do NOT delete or integrate into new system.
EOF

# 3. 检查依赖
grep -r "from.*workspace\|import.*workspace" frontend/ui --exclude-dir=workspace
grep -r "from.*login\|import.*login" frontend/ui --exclude-dir=login
grep -r "from.*signup\|import.*signup" frontend/ui --exclude-dir=signup

# 4. 删除（如果没有依赖）
rm -rf frontend/ui/modules/workspace
rm -rf frontend/ui/modules/login
rm -rf frontend/ui/modules/signup

# 5. 验证
ls frontend/ui/core                                    # 应该存在
ls frontend/ui/modules/chessboard                     # 应该存在
ls frontend/ui/modules/games/README.md                # 应该存在
ls frontend/ui/modules/workspace 2>&1 | grep "No such file"  # 应该不存在
ls frontend/ui/modules/login 2>&1 | grep "No such file"      # 应该不存在
ls frontend/ui/modules/signup 2>&1 | grep "No such file"     # 应该不存在

# 6. 提交
git add -A
git commit -m "chore: Stage 0 - cleanup legacy modules

- Archived: games/ (Hetzner server)
- Deleted: workspace/, login/, signup/ (will rewrite)
- Preserved: core/, chessboard/ (used by new system)
"
git tag stage0-complete
```

**复制上面的命令，执行即可完成 Stage 0。**
