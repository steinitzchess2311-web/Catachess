# Stage 01 Completion Report: Enter Study Chapter Resolution

## 1. Resolution Flow
- **`patch/PatchStudyPage.tsx`**:
    - 进入 patch study 时先调用 legacy `GET /api/v1/workspace/studies/{id}` 获取章节列表。
    - 若无章节，调用 `POST /api/v1/workspace/studies/{id}/chapters` 创建默认章节。
    - 使用 chapterId 调用 `GET /study-patch/chapter/{chapter_id}/tree` 拉取 tree。
    - tree.json 缺失则 `PUT /study-patch/chapter/{chapter_id}/tree` 初始化空树。

## 2. 默认规则
- **默认标题**: `Chapter 1`
- **默认顺序**: 由 legacy 后端按已有章节数决定（首章为 0）
- **startFen**: 使用标准起始局面（STARTING_FEN）

## 3. 错误处理
- 任何步骤失败都会触发 `LOAD_ERROR` 并停止进入流程。
