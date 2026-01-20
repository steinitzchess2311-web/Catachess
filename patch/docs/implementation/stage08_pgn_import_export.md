Stage 08 - PGN 导入/导出

目标
- 导入：PGN -> tree
- 导出：tree -> PGN（仅导出，不写入存储）

必须参照的代码路径
- `patch/pgn/import.ts`
- `patch/pgn/export.ts`
- 现有 PGN 解析工具：`backend/core/real_pgn/parser.py`, `backend/core/real_pgn/builder.py`

硬性约束
- PGN 仅导入/导出，不作为编辑存储。

- 导入后 tree 必须符合 `patch/tree/type.ts` 的版本规则。

进度记录
- 完成一个 checkbox 立刻打勾。
- 完成整 stage 后必须在 `patch/docs/summary/Codex_stage08.md` 写报告。

Checklist
- [x] 在 `patch/pgn/import.ts` 定义 `importPgn(pgn: string): PgnParseResult`。
- [x] 导入逻辑必须只保留 SAN，不落 FEN。
- [x] headers 作为导入结果返回，不写入 tree.json。
- [x] 在 `patch/pgn/export.ts` 定义 `exportPgn(tree: StudyTree): PgnExportResult`。
- [x] 导出时使用传入 headers + `tree.meta.result`。
- [x] 遇到不合法 PGN 必须返回明确错误信息。
- [x] 在 UI 入口添加“导入/导出”按钮占位（不做持久化）。
- [x] 在 `patch/docs/summary/Codex_stage08.md` 写完成报告。
