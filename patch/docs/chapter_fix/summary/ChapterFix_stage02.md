# Stage 02 Completion Report: Idempotency + Permissions

## 1. Idempotent Chapter Creation
- **`patch/PatchStudyPage.tsx`**:
    - 先通过 legacy 章节列表作为来源。
    - 无章节时调用创建；若创建失败则重新拉取章节列表并复用已有章，避免并发重复创建。

## 2. Permission Handling
- 章节列表请求失败即中止进入流程，抛出 `LOAD_ERROR`，不会继续创建或写 tree.json。

## 3. 写入保护
- 只有在拿到有效 chapterId 后才会调用 tree.json 初始化与加载。
