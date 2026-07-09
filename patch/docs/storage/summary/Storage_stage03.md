# Stage 03 Completion Report: Safety + Observability
Created at: 2026-07-08 22:15 EDT
Created by: Codex
Last Modified at: 2026-07-08 22:15 EDT
Last Modified by: Codex

## 1. Concurrency Guard (Best-effort)
- **`patch/studyContext.tsx`**:
    - 计算 tree 的 SHA-256（浏览器 `crypto.subtle`），写入 `X-Tree-Hash` 请求头。
    - 保存成功后记录 `lastSavedHash`，避免重复写入。
    - 自动保存间隔为 2 秒。
    - 同一 StudyProvider 同时只允许一个保存请求；请求期间发生的新编辑会合并为请求结束后的下一次保存。
    - 旧 tree 快照保存成功时，如果当前 tree 已经变化，不会清除 `isDirty`。
- **`patch/tree/studyReducer.ts`**:
    - `MARK_SAVED` 支持 `keepDirty`，用于保护保存期间产生的新编辑。

## 2. Observability
- **`patch/studyContext.tsx`**:
    - 保存开始/成功打印 `console.info`。
- **`patch/backend/study/api.py`**:
    - 记录接收到的 `X-Tree-Hash`（若存在）。
    - 当 R2 metadata 证明 canonical 内容 hash 或已验证 `X-Tree-Hash` 未变化时，跳过重复写入并记录日志。

## 3. 失败重试行为
- 保存失败保持 `isDirty=true`，可手动或自动重试。
- 保存中产生的新编辑会排队保存，不会因为正在保存而被丢弃。

## 4. Trade-offs
- 仅为前端“最佳努力”防覆盖；服务端不强制校验 hash，以保持 tree.json schema 不变。
- 当前改动降低请求堆积和重复写入风险，但不解决多人同时编辑的冲突合并；该能力归入后续 study viewer/modifier 与实时协同设计。
