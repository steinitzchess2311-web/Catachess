# FEN Import 实施计划

## 📋 目标

实现从任意棋局位置开始创建 Study Chapter 的功能，支持：
- ✅ Import FEN 字符串创建 Chapter
- ✅ 从自定义局面开始录入/分析棋谱
- ✅ 残局练习、中局训练等场景
- ✅ 兼容 Lichess 的 FromPosition 导入方式

---

## 🎯 核心设计原则

### 1. **存储分离**（参考 Lichess）
```
Chapter Metadata (Postgres)     tree.json (R2)
┌─────────────────────┐         ┌──────────────────┐
│ id, title, ...      │         │ version: "v1"    │
│ starting_fen: str?  │────────▶│ nodes: {...}     │
│   - None = 标准局面 │         │   只存 SAN       │
│   - "..." = 自定义  │         │   不存 FEN       │
└─────────────────────┘         └──────────────────┘
```

### 2. **FEN 计算方式**
```typescript
// ✅ 正确：从 starting_fen replay
const chess = new Chess(chapter.starting_fen || STANDARD_FEN);
walkTree(tree.rootId, (node) => {
  if (node.san) chess.move(node.san);
});
const currentFen = chess.fen();

// ❌ 错误：不在 tree.json 中存储 FEN
```

### 3. **向后兼容**
- `starting_fen = NULL` → 标准起始局面（现有 chapters 默认值）
- `starting_fen = "..."` → 自定义局面

---

## 📐 架构设计

### **数据流**

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Frontend: Import FEN                                      │
│    - User pastes FEN string                                  │
│    - chess.js validates FEN                                  │
│    - Create empty tree (root only)                           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Backend: Create Chapter                                   │
│    - Save starting_fen to Postgres                           │
│    - Upload tree.json to R2                                  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. Frontend: Load Chapter                                    │
│    - Fetch chapter metadata (get starting_fen)               │
│    - Fetch tree.json from R2                                 │
│    - chess = new Chess(starting_fen)                         │
│    - Replay moves to compute FEN                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ 实施步骤

### **Phase 1: Database Schema** ⏱️ 0.5天

#### 1.1 创建数据库迁移
**文件**: `backend/modules/workspace/db/migrations/versions/XXX_add_starting_fen.py`

```python
"""Add starting_fen to chapters

Revision ID: XXX
Create Date: 2025-02-15
"""

def upgrade():
    op.add_column(
        'chapters',
        sa.Column('starting_fen', sa.String(100), nullable=True)
    )
    op.create_index(
        'ix_chapters_starting_fen',
        'chapters',
        ['starting_fen']
    )

def downgrade():
    op.drop_index('ix_chapters_starting_fen')
    op.drop_column('chapters', 'starting_fen')
```

#### 1.2 更新表定义
**文件**: `backend/modules/workspace/db/tables/studies.py`

```python
class Chapter(Base, TimestampMixin):
    # ... 现有字段 ...

    # ✅ 新增：自定义起始局面
    starting_fen: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Custom starting position (NULL = standard starting position)"
    )
```

**验收**：
- [ ] 运行 `alembic upgrade head` 成功
- [ ] 数据库中 `chapters` 表有 `starting_fen` 列
- [ ] 索引 `ix_chapters_starting_fen` 创建成功

---

### **Phase 2: Backend Models & APIs** ⏱️ 1天

#### 2.1 更新 Domain Model
**文件**: `backend/modules/workspace/domain/models/chapter.py`

```python
@dataclass
class ChapterModel:
    # ... 现有字段 ...
    starting_fen: str | None  # ✅ 新增

    @property
    def is_from_custom_position(self) -> bool:
        """Check if chapter starts from custom FEN."""
        return self.starting_fen is not None

@dataclass
class AddChapterCommand:
    # ... 现有字段 ...
    starting_fen: str | None = None  # ✅ 新增
```

#### 2.2 更新 Repository
**文件**: `backend/modules/workspace/db/repos/study_repo.py`

```python
async def create_chapter(self, command: AddChapterCommand) -> ChapterModel:
    chapter = Chapter(
        # ... 现有字段 ...
        starting_fen=command.starting_fen,  # ✅ 新增
    )
    # ...
```

#### 2.3 更新 API DTOs
**文件**: `patch/backend/study/models.py`

```python
from pydantic import field_validator

class ChapterMetadataDTO(BaseModel):
    id: str
    title: str
    # ... 现有字段 ...
    starting_fen: Optional[str] = None  # ✅ 新增

    @field_validator('starting_fen')
    @classmethod
    def validate_fen(cls, v: Optional[str]) -> Optional[str]:
        """Validate FEN format."""
        if v is None:
            return None

        # 基础验证：至少 4 个部分
        parts = v.split()
        if len(parts) < 4:
            raise ValueError("Invalid FEN: must have at least 4 parts")

        return v

class ChapterCreateDTO(BaseModel):
    title: str
    starting_fen: Optional[str] = None  # ✅ 新增
```

#### 2.4 更新 API Endpoints
**文件**: `backend/modules/workspace/api/endpoints/studies.py`

```python
@router.post("/studies/{study_id}/chapters")
async def create_chapter(
    study_id: str,
    data: ChapterCreateDTO,  # ✅ 现在包含 starting_fen
    # ...
):
    command = AddChapterCommand(
        study_id=study_id,
        title=data.title,
        starting_fen=data.starting_fen,  # ✅ 传递
        # ...
    )
    # ...
```

**验收**：
- [ ] POST `/api/v1/workspace/studies/{id}/chapters` 接受 `starting_fen` 参数
- [ ] GET `/api/v1/workspace/studies/{study_id}/chapters/{id}` 返回 `starting_fen`
- [ ] 无效 FEN 返回 400 错误

---

### **Phase 3: Frontend - Import FEN** ⏱️ 1天

#### 3.1 添加 FEN 导入函数
**文件**: `patch/pgn/import.ts`

```typescript
/**
 * Standard starting position FEN
 */
export const STANDARD_STARTING_FEN =
  'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1';

/**
 * Check if FEN is standard starting position
 */
export function isStandardStartingFen(fen: string): boolean {
  return fen === STANDARD_STARTING_FEN;
}

/**
 * Import FEN - creates an empty tree with custom starting position
 */
export function importFromFen(fenString: string): PgnParseResult {
  // Validate FEN using chess.js
  const validation = Chess.validateFen(fenString);

  if (!validation.ok) {
    return {
      success: false,
      tree: null,
      headers: {},
      errors: [validation.error || 'Invalid FEN string']
    };
  }

  // Create chess instance to verify FEN is playable
  try {
    const chess = new Chess(fenString);

    // Create empty tree (only root node)
    const tree = createEmptyTree();
    tree.meta.result = null;

    return {
      success: true,
      tree,
      headers: { FEN: fenString },
      startingFen: fenString,  // ✅ Pass to caller
      errors: []
    };
  } catch (error) {
    return {
      success: false,
      tree: null,
      headers: {},
      errors: [(error as Error).message || 'Failed to parse FEN']
    };
  }
}
```

#### 3.2 更新 PgnParseResult 类型
**文件**: `patch/pgn/import.ts`

```typescript
export interface PgnParseResult {
  success: boolean;
  tree: StudyTree | null;
  headers: Record<string, string>;
  startingFen?: string;  // ✅ 新增：需要保存到 chapter metadata
  errors: string[];
}
```

#### 3.3 添加 Import FEN UI
**文件**: `patch/sidebar/movetree.tsx`

```typescript
export function MoveTree({ className }: MoveTreeProps) {
  const { loadTree, setError, clearError } = useStudy();

  const handleImportFenClick = () => {
    const fenString = window.prompt(
      'Paste FEN string:\n\n' +
      'Example: rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
    );

    if (!fenString) return;

    clearError();
    const result = importFromFen(fenString);

    if (!result.success || !result.tree) {
      const message = result.errors.length > 0
        ? result.errors.join('; ')
        : 'Failed to import FEN';
      setError('LOAD_ERROR', message, { errors: result.errors });
      return;
    }

    // Load tree with starting FEN
    loadTree(result.tree, result.startingFen);
  };

  return (
    <div className={`move-tree-container ${className || ''}`}>
      <div className="move-tree-title">
        <span>Move Tree</span>
        <div className="tree-controls">
          <button onClick={handleImportPgnClick}>Import PGN</button>
          <button onClick={handleImportFenClick}>Import FEN</button>  {/* ✅ 新增 */}
        </div>
      </div>
      {/* ... */}
    </div>
  );
}
```

#### 3.4 更新 Study Context
**文件**: `patch/studyContext.tsx`

```typescript
interface StudyState {
  chapterId: string | null;
  tree: StudyTree | null;
  cursorNodeId: string | null;
  startingFen: string;  // ✅ 新增
  // ...
}

function loadTree(tree: StudyTree, startingFen?: string) {
  setState({
    tree,
    startingFen: startingFen || STANDARD_STARTING_FEN,  // ✅
    cursorNodeId: tree.rootId,
    // ...
  });
}

async function loadChapter(chapterId: string) {
  // 1. Get chapter metadata (includes starting_fen)
  const chapterMeta = await api.get(`/api/v1/workspace/studies/${studyId}/chapters/${chapterId}`);

  // 2. Get tree.json
  const treeResponse = await api.get(`/study-patch/chapter/${chapterId}/tree`);

  setState({
    chapterId,
    tree: treeResponse.tree,
    startingFen: chapterMeta.starting_fen || STANDARD_STARTING_FEN,  // ✅
    cursorNodeId: treeResponse.tree.rootId,
  });
}

// ✅ 计算节点的 FEN（从 starting_fen 开始 replay）
function getFenAtNode(nodeId: string): string {
  const { tree, startingFen } = state;
  const chess = new Chess(startingFen);  // ✅ 使用 starting_fen

  const path = getPathToNode(tree, nodeId);
  for (const node of path) {
    if (node.san) {
      chess.move(node.san);
    }
  }

  return chess.fen();
}
```

**验收**：
- [ ] 点击 "Import FEN" 按钮弹出输入框
- [ ] 输入有效 FEN 后创建空树
- [ ] 输入无效 FEN 显示错误提示
- [ ] 导入后可以手动添加着法

---

### **Phase 4: Integration & Testing** ⏱️ 0.5天

#### 4.1 端到端测试场景

**测试 1: 标准起始局面**
```
输入：不输入 FEN（或输入标准 FEN）
预期：
- chapter.starting_fen = NULL
- 可以正常添加着法
- FEN 计算正确
```

**测试 2: 自定义局面（车兵残局）**
```
输入：r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1
预期：
- chapter.starting_fen = "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"
- Root 后的第一步从车兵残局开始
- 棋盘显示正确位置
- FEN replay 正确
```

**测试 3: 黑方先走**
```
输入：rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1
预期：
- 黑方可以走棋
- 轮到黑方的标记正确
```

**测试 4: 无效 FEN**
```
输入：invalid fen string
预期：
- 显示错误提示
- 不创建 chapter
```

#### 4.2 单元测试

**文件**: `patch/pgn/import.test.ts`

```typescript
describe('importFromFen', () => {
  it('should accept standard starting position', () => {
    const result = importFromFen(STANDARD_STARTING_FEN);
    expect(result.success).toBe(true);
    expect(result.startingFen).toBe(STANDARD_STARTING_FEN);
    expect(result.tree?.nodes[result.tree.rootId].children).toHaveLength(0);
  });

  it('should accept custom FEN', () => {
    const fen = 'r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1';
    const result = importFromFen(fen);
    expect(result.success).toBe(true);
    expect(result.startingFen).toBe(fen);
  });

  it('should reject invalid FEN', () => {
    const result = importFromFen('invalid');
    expect(result.success).toBe(false);
    expect(result.errors.length).toBeGreaterThan(0);
  });
});
```

**验收**：
- [ ] 所有单元测试通过
- [ ] 端到端测试场景通过
- [ ] 无回归错误（现有功能正常）

---

## 📁 文件清单

### **新增文件**
```
backend/modules/workspace/db/migrations/versions/
  └── XXX_add_starting_fen.py              [新增] 数据库迁移

patch/pgn/import.test.ts                   [新增] 单元测试
```

### **修改文件**
```
backend/modules/workspace/db/tables/studies.py
  ├── Chapter.starting_fen                 [新增字段]
  └── __table_args__                       [新增索引]

backend/modules/workspace/domain/models/chapter.py
  ├── ChapterModel.starting_fen            [新增字段]
  ├── ChapterModel.is_from_custom_position [新增方法]
  └── AddChapterCommand.starting_fen       [新增字段]

backend/modules/workspace/db/repos/study_repo.py
  └── create_chapter()                     [传递 starting_fen]

patch/backend/study/models.py
  ├── ChapterMetadataDTO.starting_fen      [新增字段]
  ├── validate_fen()                       [新增验证器]
  └── ChapterCreateDTO.starting_fen        [新增字段]

backend/modules/workspace/api/endpoints/studies.py
  ├── create_chapter()                     [接受 starting_fen]
  └── get_chapter()                        [返回 starting_fen]

patch/pgn/import.ts
  ├── STANDARD_STARTING_FEN                [新增常量]
  ├── isStandardStartingFen()              [新增函数]
  ├── importFromFen()                      [新增函数]
  └── PgnParseResult.startingFen           [新增字段]

patch/sidebar/movetree.tsx
  └── handleImportFenClick()               [新增处理器]

patch/studyContext.tsx
  ├── StudyState.startingFen               [新增状态]
  ├── loadTree()                           [接受 startingFen 参数]
  ├── loadChapter()                        [读取 starting_fen]
  └── getFenAtNode()                       [使用 starting_fen replay]
```

---

## 📊 进度追踪

| Phase | 任务 | 预计时间 | 状态 | 负责人 |
|-------|------|----------|------|--------|
| 1 | Database Schema | 0.5天 | ⬜ Todo | - |
| 1.1 | 创建迁移文件 | - | ⬜ | - |
| 1.2 | 更新表定义 | - | ⬜ | - |
| 1.3 | 运行迁移 | - | ⬜ | - |
| 2 | Backend Models & APIs | 1天 | ⬜ Todo | - |
| 2.1 | 更新 Domain Model | - | ⬜ | - |
| 2.2 | 更新 Repository | - | ⬜ | - |
| 2.3 | 更新 API DTOs | - | ⬜ | - |
| 2.4 | 更新 API Endpoints | - | ⬜ | - |
| 3 | Frontend - Import FEN | 1天 | ⬜ Todo | - |
| 3.1 | 添加 importFromFen() | - | ⬜ | - |
| 3.2 | 更新 PgnParseResult | - | ⬜ | - |
| 3.3 | 添加 Import FEN UI | - | ⬜ | - |
| 3.4 | 更新 Study Context | - | ⬜ | - |
| 4 | Integration & Testing | 0.5天 | ⬜ Todo | - |
| 4.1 | 端到端测试 | - | ⬜ | - |
| 4.2 | 单元测试 | - | ⬜ | - |

**总计**: 3天

---

## ✅ 验收标准

### **功能验收**
- [ ] 用户可以通过 "Import FEN" 按钮导入任意 FEN 局面
- [ ] 导入后创建空 Chapter，starting_fen 正确保存到数据库
- [ ] 可以在导入的局面基础上添加着法
- [ ] 棋盘显示的位置与 FEN 一致
- [ ] FEN 计算（replay）正确，包括：
  - [ ] 标准起始局面
  - [ ] 自定义局面
  - [ ] 黑方先走的局面
- [ ] 无效 FEN 输入时显示友好错误提示

### **技术验收**
- [ ] 数据库迁移成功，无错误
- [ ] API 接受和返回 `starting_fen` 字段
- [ ] `starting_fen = NULL` 表示标准起始局面（向后兼容）
- [ ] tree.json 仍然只存 SAN，不存 FEN
- [ ] 单元测试覆盖率 > 80%
- [ ] 无 TypeScript 类型错误
- [ ] 无 ESLint 警告

### **性能验收**
- [ ] FEN 验证 < 100ms
- [ ] Import FEN 响应时间 < 500ms
- [ ] Replay 100 步棋 < 200ms

---

## 🔮 未来扩展

### **Phase 2+: PGN Import with Variations**
- 使用 `@mliebelt/pgn-parser` 或 `chess-ops`
- 支持 variations、comments、NAGs
- 详见独立文档：`pgn_import_advanced.md`

### **可选功能**
- [ ] FEN 可视化编辑器（拖拽放置棋子）
- [ ] 从图片识别棋盘位置
- [ ] FEN 历史记录（最近使用的 FEN）
- [ ] 常见残局模板（King vs King+Queen, etc.）

---

## 📚 参考资料

- **Lichess 实现**: `lichess_pgn_fen.md`
- **chess.js 文档**: https://github.com/jhlywa/chess.js
- **FEN 格式**: https://en.wikipedia.org/wiki/Forsyth%E2%80%93Edwards_Notation
- **PGN 标准**: http://www.saremba.de/chessgml/standards/pgn/pgn-complete.htm

---

## 📝 备注

### **设计决策记录**

**Q: 为什么不在 tree.json 中存储 FEN？**
- A: 参考 Lichess 架构，FEN 可以通过 replay 计算，无需存储。这样：
  - 节省存储空间
  - 避免 FEN 与 SAN 不一致的问题
  - 简化数据结构

**Q: 为什么 starting_fen 允许 NULL？**
- A: NULL 表示标准起始局面，节省存储空间。大部分 Chapter 都是标准起始局面，不需要存储完整 FEN 字符串。

**Q: 如何处理 Chess960？**
- A: Chess960 的起始 FEN 也存储在 `starting_fen` 中。未来可以添加 `variant` 字段区分变体。

---

**文档版本**: 1.0
**创建日期**: 2025-02-15
**最后更新**: 2025-02-15
