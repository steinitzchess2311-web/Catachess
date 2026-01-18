# Stage 1 - 核心 PGN 引擎（NodeTree / PGN / Show / FEN）

本文件是 Stage 1 的概览。更细拆分见：`stage1a.md`、`stage1b.md`、`stage1c.md`。

## 约束（必须写在每个 stage 文档开头）
- [ ] 每完成一项任务，必须勾选对应 checkbox。
- [ ] 如果遇到阻塞或不确定，必须直接写明问题，不允许猜测后勾选。
- [ ] 禁止“先勾选后补做”。
- [ ] 禁止谎报进度；我会抽查对比代码。

---

## 本 Stage 目标
在 `backend/core/real_pgn/` 建立可复用的核心算法层：
- NodeTree 数据结构
- PGN 序列化/反序列化
- ShowDTO 渲染
- FEN 计算与校验

本阶段不接 DB、不接 R2、不改 API。

---

## 分计划（Checklist）

### A. 建立模块骨架与公共类型
- [ ] 新建目录 `backend/core/real_pgn/`（若不存在）。
- [ ] 新建 `backend/core/real_pgn/__init__.py`，暴露核心 API（先留空也可）。
- [ ] 新建 `backend/core/real_pgn/models.py`：
  - [ ] 定义 `PgnNode`（包含 node_id、parent_id、san、uci、ply、move_number、comment_before、comment_after、nags、main_child、variations、fen）。
  - [ ] 定义 `NodeTree`（nodes dict + root_id + headers/meta）。
  - [ ] 定义 `GameMeta`（headers / result / setup_fen / startpos 处理）。
  - [ ] 保持字段与 DB 可映射（不引入 DB 特有字段）。

### B. PGN Builder（NodeTree -> PGN）
- [ ] 新建 `backend/core/real_pgn/builder.py`。
- [ ] 编写 `build_pgn(tree: NodeTree) -> str`：
  - [ ] 输出 PGN headers（Event/Site/Date/White/Black/Result 等）。
  - [ ] 处理 SetUp "1" + FEN（非起始局面）。
  - [ ] movetext 生成规则：
    - [ ] 白方走子必带回合号（"1. e4"）。
    - [ ] 黑方起手带 "1..."。
    - [ ] NAG 输出为 "$x" 形式。
    - [ ] comment_before / comment_after 均输出为 `{...}`。
    - [ ] variation 输出为 `( ... )`，嵌套可支持。
  - [ ] 末尾结果标记输出（Result 或 *）。
- [ ] 与现有 `backend/modules/workspace/pgn/serializer/to_pgn.py` 对比输出（仅对照，不替换）。

### C. PGN Parser（PGN -> NodeTree）
- [ ] 新建 `backend/core/real_pgn/parser.py`。
- [ ] 使用 python-chess 解析 PGN 到 GameNode。
- [ ] 编写 `parse_pgn(pgn_text: str) -> NodeTree`：
  - [ ] 保留 headers 与 result。
  - [ ] 构建 NodeTree：
    - [ ] node_id 生成策略：使用稳定 id（如 ULID/uuid），避免依赖顺序。
    - [ ] 主线/变化树结构正确。
    - [ ] 支持多层 variation。
    - [ ] 读取 comment 与 NAG。
- [ ] 对不合法 PGN 返回明确错误（抛异常）。

### D. ShowDTO（NodeTree -> 前端渲染结构）
- [ ] 新建 `backend/core/real_pgn/show.py`。
- [ ] 编写 `build_show(tree: NodeTree) -> dict`：
  - [ ] `headers` 按 key/value 数组输出。
  - [ ] `nodes` 映射 node_id -> 节点详情（含 san/fen/comment/nags）。
  - [ ] `render` 生成 token 流：
    - [ ] 主线顺序 token
    - [ ] variation start/end token
    - [ ] comment token
- [ ] 保证 token 顺序可直接用于 UI 渲染（无需额外解析）。

### E. FEN 计算与校验
- [ ] 新建 `backend/core/real_pgn/fen.py`。
- [ ] 编写 `apply_move(parent_fen, move_san|uci) -> fen`：
  - [ ] 使用 python-chess 校验合法性。
  - [ ] 返回新 FEN、ply、move_number。
- [ ] 编写 `build_fen_index(tree: NodeTree) -> dict[node_id, fen]`。
- [ ] 支持 SetUp/FEN 初始局面。

### F. 最小测试与对照（不改现有测试）
- [ ] 使用 `backend/modules/workspace/pgn/tests_vectors/*` 手动对照：
  - [ ] 复杂变例
  - [ ] 大量注释
  - [ ] 非标准起始局面
- [ ] 记录对照结果（不需要写测试，但要写结果）。

---

## 输出物（本阶段交付）
- `backend/core/real_pgn/models.py`
- `backend/core/real_pgn/builder.py`
- `backend/core/real_pgn/parser.py`
- `backend/core/real_pgn/show.py`
- `backend/core/real_pgn/fen.py`
