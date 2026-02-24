Catachess 架构更新总览 

目标（必须同时达成）
- 这是 study（研讨）产品，不是对弈平台。
- 本地编辑与存储使用 tree.json；PGN 仅用于导入/导出。
- chess.js 只用于校验与 replay，不参与存储结构。
- FEN 不长期存储，仅运行态生成；节点只存 SAN。
- 后端不参与走法计算；tree 构建与变体操作在前端完成。
- 单 chapter 单 tree；tree.json 含版本号。
- Postgres 不持有 tree 内容；R2 与 chapter_id 对齐。
- 引擎调用改为 `https://lichess.org/api/cloud-eval`，结果不落库。

补丁范围（vertical slice）
- 前端：`patch/studyContext.tsx`, `patch/board/studyBoard.tsx`, `patch/tree/*`, `patch/chessJS/*`, `patch/pgn/*`, `patch/sidebar/*`
- 后端：`patch/backend/study/models.py`, `patch/backend/study/api.py`
- 存储：`backend/modules/workspace/pgn_v2/repo.py` 与 `backend/modules/workspace/domain/services/pgn_sync_service.py` 改为 tree.json 为主

与 legacy 的连接点
- R2 key 统一走 `backend/modules/workspace/storage/keys.py`（章节 key 必须是 `chapters/{chapter_id}.tree.json`）。
- 保留 legacy PGN 解析/导出能力作为兼容（`backend/core/real_pgn/*`）。
- 前端新增入口切到 patch 组件，legacy 入口保留用于回退对比。

核心数据流（Study）
User Drag Piece
      │
StudyBoard.tsx (react-chessboard)
      │  onPieceDrop(from, to)
      │
StudyContext.dispatch(ADD_MOVE)
      │
StudyTree.addMove()
  - 校验当前 cursor
  - 若已有子节点 → 分支
  - 新建 node（只存 SAN）
      │
Cursor.update(nodeId)
      │
replay.ts（chess.js）
  - 回放 SAN path
      │
fen.ts（生成 FEN）
      │
StudyBoard re-render

落地要求
- patch/docs/improved_plan.md：完整改进方案（含目录结构与连接点）。
- patch/docs/implementation/：按 stage 拆分的极细化落地方案（带 checklist）。
- patch/docs/summary/：每个 stage 完成后由执行人提交报告。
