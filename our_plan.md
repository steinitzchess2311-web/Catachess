# 我们的 PGN 重构计划（our_plan.md）

目标：以现有代码为第一优先级，把 `docs/pgn/plan.md` 的思想落到当前工程里，最小改动完成“可用且可持续”的新 PGN 体系。  
核心原则：走法树（Node Tree）是唯一真相源；PGN 只是序列化输出；每个节点必须有 FEN。

下面的计划严格以当前代码为主，参考 `docs/pgn/plan.md` 作为方向，而不是照搬目录或模型。

---

## 0. 现状梳理（以当前代码为主）

### 已有但将弃用的 PGN 处理器（不删，只迁移）
- `backend/modules/workspace/pgn/serializer/*`  
  负责 VariationNode <-> PGN，依赖 `to_tree.py`/`to_pgn.py`。  
  已使用但结构老旧，且与未来功能（完整注释/NAG/前端渲染）不匹配。
- `backend/core/chess_basic/pgn/*`  
  用于 `backend/core/orchestration/*` 记录对局，主要服务“实时对弈”场景，无法满足 Study/注释/变例 UI 需求。

### 必须保留并作为新体系基础的模块
- `backend/core/new_pgn/*`  
  只用于 PGN 检测/拆分（多盘 PGN 导入），不与“编辑/渲染”体系冲突，应继续保留。
- `backend/modules/workspace`  
  这是 Study 的主战场：  
  - 数据表：`backend/modules/workspace/db/tables/variations.py`  
    已有 move tree（parent_id / rank / fen / san / uci），说明“走法树”已在数据库中存在。  
  - PGN 同步：`backend/modules/workspace/domain/services/pgn_sync_service.py`  
    目前依赖旧 serializer 生成 PGN 并写入 R2。  
  - API 入口：`backend/modules/workspace/api/endpoints/studies.py`  
    现有 move/variation/annotation 增删改接口，前端正在使用。
- R2 存储规范：`backend/modules/workspace/storage/keys.py`  
  目前使用 `chapters/{chapter_id}.pgn` 保存章节 PGN。

### 当前关键问题（以代码现状为基线）
1. 旧 PGN 处理器无法覆盖“注释/变例/前端渲染/增量 FEN”等功能需求。  
2. 走法树已在 DB 中存在，但 PGN 输出与前端展示的数据结构不够“像 lichess”。  
3. 前端与后端缺少统一的“Node Tree -> ShowDTO”输出。  
4. FEN 目前来自客户端输入，缺乏服务端验证与重算能力。  

---

## 1. 目标范围（优先级说明）

### 这次要完成的（必须贴合现有代码）
- 新 PGN 体系（NodeTree + Serializer + ShowDTO + FEN Index）。  
- 与现有 Study/Chapter/Variation 表结构对齐的实现。  
- R2 快照输出（继续使用 `chapters/{chapter_id}.pgn`，新增 tree/fen_index）。  
- 可给前端直接渲染的 ShowDTO（类 lichess）。  

### 本次不做（但需预留）
- 替换 `backend/core/new_pgn` 的 PGN 检测逻辑。  
- 重写 Study/Chapter 数据模型或数据库结构的大规模迁移。  
- 从零重写前端 UI，只做 API 对接层的升级。  

---

## 2. 新系统总体架构（基于现有模块改造，而不是重建）

### 2.1 目录结构（建议，按现有模块插入）

```
backend/core/real_pgn/  # 新增：纯算法层
  __init__.py
  models.py        # NodeTree 数据结构（PgnNode / GameMeta）
  builder.py       # NodeTree -> 标准 PGN 文本
  parser.py        # PGN -> NodeTree（导入/回放）
  show.py          # NodeTree -> ShowDTO（前端渲染）
  fen.py           # FEN 计算与校验

backend/modules/workspace/pgn_v2/  # 新增：对接 DB/R2
  __init__.py
  adapters.py      # DB Variation/Annotation <-> NodeTree
  repo.py          # R2 存取：current.pgn / tree.json / fen_index.json
  service.py       # 事件应用 + 校验 + 版本管理
```

说明：
- `backend/core/real_pgn` 只做算法，不碰数据库与 R2。  
- `backend/modules/workspace/pgn_v2` 专门对接现有 Study/Chapter/Variation 表与 R2 Key 体系。  
- 旧 `backend/modules/workspace/pgn/*` 先保留，内部逐步切换到新实现。  

### 2.2 贴合现有代码的改动点（必须做的最小改动）
- `backend/modules/workspace/domain/services/pgn_sync_service.py`  
  - 由 `modules.workspace.pgn.serializer.*` 改为 `backend/core/real_pgn/builder.py`  
  - 仍然输出 `chapters/{chapter_id}.pgn`，并新增写入 tree/fen_index  
- `backend/modules/workspace/domain/services/chapter_import_service.py`  
  - 导入 PGN 时，调用 `backend/core/real_pgn/parser.py` -> NodeTree  
  - 通过适配器写入 `variations` / `move_annotations`  
  - 继续使用 `backend/core/new_pgn` 做拆分检测  
- `backend/modules/workspace/domain/services/study_service.py`  
  - `add_move` 时不再依赖前端传 `fen`  
  - 使用 `backend/core/real_pgn/fen.py` 计算 fen + ply  
- `backend/modules/workspace/pgn/serializer/*`  
  - 标记 legacy，仅保留用于回归对比与旧接口  
- `backend/modules/workspace/api/endpoints/studies.py`  
  - 新增 `/show`、`/fen`  
  - 现有路由保持，内部切换到新 service  

---

## 3. 数据模型（NodeTree 与现有表对齐，不改 DB 结构）

### 3.1 NodeTree 目标结构（最小补齐当前字段）
（参考 `docs/pgn/plan.md`，但与当前 DB 字段对齐）

```
PgnNode
  node_id: str
  parent_id: str | None
  san: str | None
  uci: str | None
  ply: int
  move_number: int
  comment_before: str | None
  comment_after: str | None
  nags: list[int]
  main_child: str | None
  variations: list[str]
  fen: str
```

### 3.2 与当前 DB 的映射（直接映射，不引入新表）
- `variations.id` -> `node_id`  
- `variations.parent_id` -> `parent_id`  
- `variations.san / uci / move_number / fen / rank` -> 主体字段  
- `move_annotations.text / nag` -> comment_after / nags  
- `rank=0` 为主线，`rank>0` 为 variation 起点  

### 3.3 结论
走法树已经在 DB 中存在（`variations` + `move_annotations`）。  
本次改造不改 DB，只新增“NodeTree 逻辑层”与“统一序列化/渲染输出”。  

---

## 4. PGN 输出（NodeTree -> PGN，替换现有 serializer）

### 4.1 新 builder 规则
- 标准 PGN 兼容（ChessBase/Lichess 可导入）  
- 注释用 `{...}`  
- 变例用 `(...)`  
- NAG 使用 `$` 数字形式（如 `$1`）  
- 终局标记必须写入（`1-0 / 0-1 / 1/2-1/2 / *`）  
- 保留 `SetUp "1"` + `FEN "..."`（非起始局面）

### 4.2 对应现有接口（必须替换）
- `backend/modules/workspace/domain/services/pgn_sync_service.py`  
  改为调用新 builder，生成 current.pgn 并上传 R2。  
- `backend/modules/workspace/pgn/serializer/to_pgn.py`  
  逐步弃用，只保留用于旧测试或回归对比。  

---

## 5. ShowDTO（给前端渲染，新增接口不破坏旧接口）

### 5.1 输出结构（面向前端）

```
{
  "headers": [{"k":"Event","v":"..."}, ...],
  "root_fen": "startpos | FEN",
  "result": "1-0",
  "nodes": { "n0": {...}, "n1": {...} },
  "render": [
    {"t":"comment","node":"n0","text":"..."},
    {"t":"move","node":"n1","label":"1.","san":"Nf3"},
    {"t":"variation_start","from":"n1"},
      {"t":"move","node":"v1","label":"(2.","san":"c4"},
    {"t":"variation_end"}
  ]
}
```

### 5.2 前端对接位置（在现有 UI 上加新入口）
- `frontend/ui/modules/study/events/index.ts`  
  目前只请求 mainline + annotations，需要新增 `/show` 接口后改为消费 ShowDTO。  

---

## 6. FEN 机制（服务端统一计算，替换前端提供）

### 6.1 现状问题
- 目前 `add_move` 依赖前端传入 `fen`，与“真相源在后端”冲突。  

### 6.2 新方案（最小改造路径）
- 统一由服务端计算 FEN：  
  - 输入：`parent_node_id` + `uci` 或 `san`  
  - 输出：`fen` + `ply`  
- `backend/core/real_pgn/fen.py` 负责计算逻辑（依赖 python-chess）。  
- `fen_index.json` 输出为 `node_id -> fen`，用于前端快速跳转和分析层调用。  

---

## 7. 存储策略（R2，沿用现有 key）

### 7.1 现有 R2 结构
- `chapters/{chapter_id}.pgn`（当前 PGN）  
- 相关 Key 由 `backend/modules/workspace/storage/keys.py` 统一生成  

### 7.2 新增对象（不破坏旧 key）
- `chapters/{chapter_id}.tree.json`  
- `chapters/{chapter_id}.fen_index.json`  
- （可选）`chapters/{chapter_id}.events.jsonl`  

说明：保留现有 `chapter.r2_key` 指向 `chapters/{chapter_id}.pgn`，避免数据库迁移。

### 7.4 ID 对齐校验（必须补）
- 现状：DB 里 `chapters.r2_key` 是独立字段，未强制等于 `chapters/{chapter_id}.pgn`。  
- 风险：如果 r2_key 与 chapter_id 不一致，前端/后端会读错 PGN。  
- 计划：新增一致性校验与回填逻辑：  
  - 读章节点时校验 `chapter.r2_key == R2Keys.chapter_pgn(chapter_id)`  
  - 不一致时记录告警并回填（或仅在迁移阶段做一次性修复）  
  - 同步 tree/fen_index 时一并修复 key  

### 7.3 导入与同步（严格走现有服务）
- `backend/modules/workspace/domain/services/chapter_import_service.py`  
  - 导入 PGN 时，除上传原始 PGN 外，还需解析出 NodeTree。  
  - 生成 Variation/Annotation 数据写入 DB（优先 DB），tree.json 仅用于快照。  
- `backend/modules/workspace/domain/services/pgn_sync_service.py`  
  - 改为使用 NodeTree 统一生成 current.pgn / fen_index。  

---

## 8. 引擎分析与标签（必须纳入计划）

### 8.1 Stockfish 分析（替换占位符）
- 现状问题：当前分析入口是占位符，无法稳定消费新 FEN 索引。  
- 计划：新增“分析队列写入点”，让新体系生成 `fen_index` 后触发分析任务。  
- 建议落点：  
  - `backend/core/real_pgn/fen.py` 生成/更新 FEN 后，提交“analysis job”  
  - 由 worker 拉取 `chapters/{chapter_id}.fen_index.json` 做增量分析  

### 8.1.1 具体落文件与函数（按现有代码改造）
- Stockfish 调用入口（已有）：  
  - `backend/core/chess_engine/__init__.py:get_engine()`  
  - `backend/core/chess_engine/client.py:EngineClient.analyze()`  
  - `backend/core/chess_engine/orchestrator/orchestrator.py`（多 spot 调度）  
- 现有分析管线（PGN 文件式）：  
  - `backend/core/tagger/analysis/pipeline.py`  
  - `backend/core/tagger/analysis/pgn_processor.py`  
- 改造点（贴合新 FEN 索引）：  
  - 新增 `backend/core/tagger/analysis/fen_processor.py`  
    - 输入 `fen_index.json`，输出 `node_id + fen` 列表  
  - 在 `backend/core/tagger/analysis/pipeline.py` 增加 `run_fen_index()` 分支  
    - 读取 `fen_processor` 输出并逐点调用引擎  
  - 保留 `pgn_processor.py` 以兼容老流程，但新增路径必须优先走 fen_index  

### 8.2 Tagger predictor（与现有 tagger 代码对接）
- 现状：`backend/core/tagger/*` 依赖 PGN 文件或旧 pipeline。  
- 计划：改为消费新 FEN/NodeTree 输出，形成“节点级标签”。  
- 建议落点：  
  - 新增 `backend/core/tagger/predictor.py`（或扩展现有 pipeline）  
  - 输入：`node_id + fen + context`  
  - 输出：tag 结构写入独立表或 R2（与现有分析结果兼容）  

### 8.2.1 具体落文件与函数（按现有代码改造）
- 现有 predictor：`backend/core/tagger/pipeline/predictor/predictor.py:predict_moves()`  
  - 当前只支持单个 `fen`，并调用 `core.tagger.facade.tag_position()`  
- 需要新增的“节点级 predictor”：  
  - 文件：`backend/core/tagger/pipeline/predictor/node_predictor.py`  
  - 函数建议：`predict_node_tags(node_id: str, fen: str, move_uci: str | None)`  
  - 内部调用：`backend/core/tagger/facade.py:tag_position()`  
- 标签输出的落点（两种方案二选一）：  
  - DB：新增表（如 `move_tags`）存 `node_id/tag/score/context/version`  
  - R2：`chapters/{chapter_id}.tags.json`（按 node_id 分组）  

### 8.3 与 R2/事件流的对接
- fen_index 更新后：  
  - 写入 `chapters/{chapter_id}.fen_index.json`  
  - 追加 `chapters/{chapter_id}.events.jsonl`（可选，用于 replay/协作）  

---

## 9. 对外 API（保持现有路由，内部替换实现）

### 9.1 写接口（保持路由风格，修改内部参数来源）

- `POST /api/v1/workspace/studies/{study_id}/chapters/{chapter_id}/moves`  
  - 仍保留现有路由，但后端改为自行计算 `fen` 与 `ply`  
  - 前端仅传 `parent_id + uci|san`  

- `POST /api/v1/workspace/studies/{study_id}/chapters/{chapter_id}/comments`  
  - 新增接口可选，但内部逻辑直接写 `move_annotations`  

- `POST /api/v1/workspace/studies/{study_id}/chapters/{chapter_id}/variations`  
  - 继续沿用现有 variation 模型（rank + parent_id）  

说明：现有注释接口  
`/chapters/{chapter_id}/moves/{move_id}/annotations`  
可继续保留，内部映射到新的 comment/NAG 逻辑。

### 9.2 读接口（优先加新，不破坏旧）

- `GET /api/v1/workspace/studies/{study_id}/chapters/{chapter_id}/pgn`  
  - 返回 current.pgn（沿用现有导出逻辑，仅内部替换）  
- `GET /api/v1/workspace/studies/{study_id}/chapters/{chapter_id}/show`  
  - 返回 ShowDTO  
- `GET /api/v1/workspace/studies/{study_id}/chapters/{chapter_id}/fen?node_id=...`  
  - 返回 `{fen}`  

---

## 10. 迁移策略（从旧 PGN 处理器到新体系，以可回滚为前提）

### 10.1 逐步替换顺序（保持可回滚）
1. 新增 `backend/core/real_pgn/*`（纯逻辑层）。  
2. 新增 `backend/modules/workspace/pgn_v2/*`（DB/R2 对接）。  
3. `PgnSyncService` 切换到新 builder（保留旧实现可回滚）。  
4. 增加 `/show` API，前端可开开关切换。  
5. 通过现有测试向量对比输出一致性，再标记旧模块为 legacy。  

### 10.2 旧模块标记
- `backend/modules/workspace/pgn/*` 标记为 legacy（保留但不新增功能）。  
- `backend/core/chess_basic/pgn/*` 仅用于对弈记录，不用于 study。  

---

## 11. 详细实施步骤（按现有代码改造的可执行清单）

### Phase A: 核心数据结构与序列化
1. 新建 `backend/core/real_pgn/models.py`  
   - 定义 `PgnNode` / `NodeTree` / `GameMeta`  
2. 新建 `backend/core/real_pgn/builder.py`  
   - NodeTree -> PGN（含注释/变例/NAG）  
3. 新建 `backend/core/real_pgn/parser.py`  
   - PGN -> NodeTree（用于导入/兼容）  
4. 新建 `backend/core/real_pgn/show.py`  
   - NodeTree -> ShowDTO  

### Phase B: FEN 计算
1. 新建 `backend/core/real_pgn/fen.py`  
   - 统一 SAN/UCI 校验 + FEN 推导  
2. 写 `fen_index` 生成器  

### Phase C: DB 适配器（以 Variation 表为输入输出）
1. 新建 `backend/modules/workspace/pgn_v2/adapters.py`  
   - Variation/Annotation -> NodeTree  
   - NodeTree -> DB 变更（新增/删除/修改）  

### Phase D: R2 输出（沿用现有 key）
1. 新建 `backend/modules/workspace/pgn_v2/repo.py`  
   - 上传 current.pgn / tree.json / fen_index.json  
2. 更新 `backend/modules/workspace/storage/keys.py`  
   - 增加 tree.json / fen_index.json 的 key 生成函数  

### Phase E: API 升级（保持路由）
1. 更新 `backend/modules/workspace/api/endpoints/studies.py`  
   - 新增 `/show` 与 `/fen`  
   - 现有 add_move / add_annotation 改用新 service  

### Phase F: 前端接入（小改动接入 ShowDTO）
1. 更新 `frontend/ui/modules/study/events/index.ts`  
   - 从 `/show` 获取完整渲染数据  
   - 点击 move 直接跳 FEN  

### Phase G: Engine/Tagger 接入
1. 新增分析队列写入点（fen_index 更新触发）  
2. 更新 Stockfish worker 消费方式（增量读取 fen_index）  
3. Tagger predictor 改为节点级输入输出  

---

## 12. 测试与验收

### 必测
- 标准 PGN 导入/导出（含注释/变例/NAG）  
- FEN 索引一致性（DB vs 计算结果）  
- /show 接口渲染与前端点击跳转  
- R2 快照一致性（PGN / tree / fen_index）  

### 推荐测试文件
使用已有样例（`backend/modules/workspace/pgn/tests_vectors/*`）覆盖：  
- 深层变例  
- 大量注释  
- 非标准起始局面  
- 黑方起手变例  

---

## 13. 最终结果（目标状态）

当计划完成后，我们应当具备：
- 一套新 PGN 处理器（可替代所有旧代码）。  
- NodeTree 为唯一真相源，PGN 与 ShowDTO 可随时再生成。  
- 每个节点有 FEN，前端点击一步即可跳局面。  
- R2 存储中包含：`current.pgn + tree.json + fen_index.json`。  

---

## 14. 需要确认的开放问题

1. NodeTree 是否只基于 DB Variation，还是未来转为 R2 事件流优先？  
2. 是否需要新增 `Chapter.pgn_version` 字段用于全局乐观锁？  
3. 是否立刻替换前端的 mainline 渲染，还是先双通道并行？  
4. Tagger 标签结果写入 DB 还是 R2（是否需要新表）？  
5. Stockfish 分析结果与现有 `analysis/{game_id}.json` 的兼容方式？  
