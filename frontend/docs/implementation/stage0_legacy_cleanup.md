# Stage 0: Legacy Code Cleanup

> **Goal:** 清理遗留代码，为新架构腾出空间
> **Duration:** 1-2 小时
> **Risk:** 低（只删除/归档，不影响保留模块）
> **Prerequisites:** 无

---

## 1. 保留清单（Do NOT Delete）

以下模块**禁止删除**，新系统会使用：

### ✅ `frontend/ui/core/`
- **功能：** Window Management（drag, focus, resize）
- **保留理由：** 基础设施，代码质量好，新系统依赖

### ✅ `frontend/ui/modules/chessboard/`
- **功能：** 核心棋盘逻辑
- **保留理由：** 已模块化，符合架构标准

**验证命令：**
```bash
ls -la frontend/ui/core
ls -la frontend/ui/modules/chessboard
```

- [x] `core/` 存在
- [x] `chessboard/` 存在

---

## 2. 归档清单（Archive, Do Not Use）

### 🔒 `frontend/ui/modules/games/`
- **状态：** 运行在 Hetzner 云服务器上
- **处理方式：** 保留代码，但不集成到新系统
- **操作：** 添加 README.md 说明归档状态

**执行：**
```bash
cat > frontend/ui/modules/games/README.md << 'EOF'
# ARCHIVED MODULE - DO NOT USE

This module is **archived** and is NOT part of the new architecture.

## Status
- Running on Hetzner cloud server
- Not integrated into new frontend system
- Kept for reference only

## Important
DO NOT:
- Import this module in new code
- Deploy this module with new system
- Delete this directory (it's archived, not removed)

Last updated: 2026-01-12
EOF

# 验证
cat frontend/ui/modules/games/README.md
```

**验证：**
- [x] `games/README.md` 存在
- [x] 文件内容包含 "ARCHIVED MODULE"

---

## 3. 删除清单（Delete and Rewrite）

以下模块**必须删除**，将按新架构重写：

### 🗑️ `frontend/ui/modules/workspace/`
- **原因：** 45 个 TS 文件，结构混乱，不符合 Vertical Slice

### 🗑️ `frontend/ui/modules/login/`
- **原因：** 旧架构，不符合新标准

### 🗑️ `frontend/ui/modules/signup/`
- **原因：** 旧架构，不符合新标准

---

## 4. 执行步骤

### Step 1: 检查依赖

**删除前必须确认没有其他模块依赖这些代码：**

```bash
# 检查 workspace 依赖
echo "Checking workspace dependencies..."
grep -r "from.*workspace\|import.*workspace" frontend/ui --exclude-dir=workspace || echo "✓ No dependencies found"

# 检查 login 依赖
echo "Checking login dependencies..."
grep -r "from.*login\|import.*login" frontend/ui --exclude-dir=login || echo "✓ No dependencies found"

# 检查 signup 依赖
echo "Checking signup dependencies..."
grep -r "from.*signup\|import.*signup" frontend/ui --exclude-dir=signup || echo "✓ No dependencies found"
```

**如果有输出：** 先移除依赖，再继续删除
**如果没有输出：** 可以安全删除

- [x] 确认没有依赖

---

### Step 2: 归档 games/

```bash
# 执行上面第 2 节的命令
cat > frontend/ui/modules/games/README.md << 'EOF'
# ARCHIVED MODULE - DO NOT USE
...（内容见第 2 节）
EOF
```

- [x] games/README.md 已创建

---

### Step 3: 删除旧模块

```bash
# 删除 workspace/
rm -rf frontend/ui/modules/workspace
echo "✓ workspace/ deleted"

# 删除 login/
rm -rf frontend/ui/modules/login
echo "✓ login/ deleted"

# 删除 signup/
rm -rf frontend/ui/modules/signup
echo "✓ signup/ deleted"
```

- [x] workspace/ 已删除
- [x] login/ 已删除
- [x] signup/ 已删除

---

## 5. 最终验证

**运行以下命令验证清理结果：**

```bash
# 应该存在（保留）
echo "=== Checking Protected Modules ==="
ls frontend/ui/core && echo "✓ core/ exists"
ls frontend/ui/modules/chessboard && echo "✓ chessboard/ exists"

# 应该存在且有 README（归档）
echo ""
echo "=== Checking Archived Module ==="
ls frontend/ui/modules/games/README.md && echo "✓ games/README.md exists"

# 不应该存在（已删除）
echo ""
echo "=== Checking Deleted Modules ==="
ls frontend/ui/modules/workspace 2>&1 | grep -q "No such file" && echo "✓ workspace/ deleted"
ls frontend/ui/modules/login 2>&1 | grep -q "No such file" && echo "✓ login/ deleted"
ls frontend/ui/modules/signup 2>&1 | grep -q "No such file" && echo "✓ signup/ deleted"

echo ""
echo "=== Stage 0 Verification Complete ==="
```

**Checklist：**
- [x] ✅ `core/` 存在
- [x] ✅ `chessboard/` 存在
- [x] ✅ `games/` 存在且有 README.md
- [x] ❌ `workspace/` 不存在
- [x] ❌ `login/` 不存在
- [x] ❌ `signup/` 不存在

---

## 6. 提交更改

```bash
git add -A
git commit -m "chore: Stage 0 - cleanup legacy modules

- Archived: games/ (kept for Hetzner server)
- Deleted: workspace/, login/, signup/ (will rewrite with new architecture)
- Preserved: core/, chessboard/ (used by new system)
"

# 打 tag
git tag -a stage0-complete -m "Stage 0: Legacy Cleanup Complete"
```

**验证：**
- [x] Git commit 成功
- [x] Tag `stage0-complete` 已创建

---

## 7. 回滚（如果需要）

**如果发现删错了：**

```bash
# 回到上一个 commit
git reset --hard HEAD~1

# 或者回到 main 分支的最新状态
git checkout main
git reset --hard origin/main
```

**注意：** git 本身就是版本控制系统，整个历史都在。不需要额外创建备份分支。

---

**Stage 0 完成！现在可以开始 Stage 1。**