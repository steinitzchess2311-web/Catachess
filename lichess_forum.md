# Lichess Forum 代码分析 & Blog 评论系统借鉴方案

> 分析对象：`backend/modules/workspace/domain/services/discussion/` 等相关模块
> 目标：为 Blog 设计一套产品级无限嵌套评论系统

---

## 一、Lichess Forum 做得好的地方

### 1. 数据模型分离清晰

三张表各司其职：

| 表 | 职责 |
|---|---|
| `discussions` | 线程（对应 blog comment 的「根评论」） |
| `discussion_replies` | 回复（嵌套层级通过 `parent_reply_id` 自引用） |
| `discussion_reactions` | 反应/点赞（`target_type` 区分是对 thread 还是 reply） |

**值得学习**：三表分离使得「给任意层级的评论点赞」、「对任意节点的回复」都不需要改表结构。

---

### 2. 无限嵌套的实现方式：自引用 FK + 深度遍历

```python
# discussion_replies.py
parent_reply_id: Mapped[str | None] = mapped_column(
    ForeignKey("discussion_replies.id", ondelete="CASCADE"),
    nullable=True,
)
quote_reply_id: Mapped[str | None] = mapped_column(
    ForeignKey("discussion_replies.id", ondelete="SET NULL"),
    nullable=True,
)
```

- `parent_reply_id` = 树形父节点，决定嵌套结构，**级联删除**
- `quote_reply_id` = 引用（类似 @某条评论），父删后 SET NULL 不影响子

**深度控制**（`nesting.py`）：通过链式向上遍历计算深度，超过 `DISCUSSION_MAX_REPLY_DEPTH`（默认5）则拒绝：

```python
async def get_reply_depth(repo, reply_id):
    depth = 0
    current_id = reply_id
    while current_id:
        depth += 1
        reply = await repo.get_by_id(current_id)
        current_id = reply.parent_reply_id
    return depth
```

**值得学习**：深度用环境变量控制，业务层校验，不是数据库层约束，灵活。

---

### 3. 乐观锁（Optimistic Locking）防并发冲突

```python
# 编辑时必须传 version，不匹配则 409
if reply.version != command.version:
    raise OptimisticLockError("Version conflict")
reply.version += 1
```

**值得学习**：评论编辑时防止「先读后写」的覆盖问题。比数据库行锁轻量，适合 HTTP API。

---

### 4. 编辑历史（Edit History）

```python
entry = {
    "content": reply.content,
    "edited_at": datetime.now(UTC).isoformat(),
    "edited_by": command.actor_id,
}
reply.edit_history = (reply.edit_history + [entry])[-10:]  # 保留最近10条
reply.edited = True
```

**值得学习**：用 JSON 字段存 history，不新建表，简单高效。`edited` boolean 标记「已编辑」让前端显示「(已编辑)」。

---

### 5. 软删除概念（通过 quote SET NULL 体现）

删父评论时：
- `parent_reply_id` → CASCADE DELETE（子评论也删）
- `quote_reply_id` → SET NULL（被引用删了，引用关系消失，但评论本身保留）

**我们可以升级**：加一个 `is_deleted BOOL` 实现软删除，父评论被删时显示「该评论已删除」，子评论仍可见（Reddit 风格）。

---

### 6. 事件总线（EventBus）解耦通知

```python
await event_bus.publish(CreateEventCommand(
    type=EventType.DISCUSSION_REPLY_ADDED,
    actor_id=command.author_id,
    target_id=reply.id,
    ...
))
```

**值得学习**：评论写入和通知（@提及、邮件）解耦，不在主流程里阻塞。我们 blog 评论可以同样设计：写评论成功 → 异步通知文章作者。

---

### 7. @Mention 提取

```python
# discussion_mentions.py（被 reply_events.py 调用）
from modules.workspace.domain.services.discussion_mentions import extract_mentions

for mention in extract_mentions(content):
    await event_bus.publish(...)
```

评论内容里的 `@username` 在提交后异步解析并发送通知事件。

---

### 8. Reactions 系统的通用设计

```python
# target_type = "thread" | "reply"
# emoji 白名单校验
ALLOWED_REACTION_EMOJIS = {"👍", "❤️", "🎯", "🚀", "👏", "🔥", "💯"}
```

`target_id + target_type` 的设计使得反应可以挂在任意层级的评论上，不需要多张表。

---

## 二、我们 Blog 评论系统的借鉴方案

### 核心原则
- **学结构，不照搬复杂度**。Lichess forum 服务 workspace 协作，我们服务博客读者，场景不同。
- **无限嵌套**，但可以配置最大深度（默认不限，产品层决定）。
- **产品级**：乐观锁、编辑历史、软删除、@提及基础都要有。

---

### 数据模型设计

**只需要两张表**（不需要 thread/reply 分离，blog 文章本身就是 "thread"）：

```sql
-- 评论表（根评论 + 嵌套回复统一存储）
CREATE TABLE blog_comments (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    article_id   UUID NOT NULL,                         -- 所属文章
    parent_id    UUID REFERENCES blog_comments(id)      -- NULL=根评论, 有值=嵌套回复
                     ON DELETE CASCADE,
    quote_id     UUID REFERENCES blog_comments(id)      -- @引用的评论
                     ON DELETE SET NULL,
    author_id    UUID NOT NULL,                         -- 登录用户 ID
    author_name  VARCHAR(100) NOT NULL,                 -- 冗余，避免 JOIN
    content      TEXT NOT NULL,
    is_deleted   BOOLEAN NOT NULL DEFAULT false,        -- 软删除（Reddit 风格）
    edited       BOOLEAN NOT NULL DEFAULT false,
    edit_history JSONB NOT NULL DEFAULT '[]',           -- [{content, edited_at}]
    version      INTEGER NOT NULL DEFAULT 1,            -- 乐观锁
    created_at   TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_blog_comments_article_id ON blog_comments(article_id);
CREATE INDEX ix_blog_comments_parent_id  ON blog_comments(parent_id);

-- 评论点赞（独立表，可复用于任意 target）
CREATE TABLE blog_comment_likes (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    comment_id UUID NOT NULL REFERENCES blog_comments(id) ON DELETE CASCADE,
    user_id    UUID NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT blog_comment_likes_unique UNIQUE (comment_id, user_id)
);

CREATE INDEX ix_blog_comment_likes_comment ON blog_comment_likes(comment_id);
```

---

### 与 Lichess 的对比

| 特性 | Lichess Forum | Blog Comments |
|---|---|---|
| 嵌套方式 | `parent_reply_id` 自引用 | 同，`parent_id` 自引用 |
| Thread/Reply 分离 | ✅ 分两张表 | ❌ 不需要，文章即 thread |
| 乐观锁 | ✅ `version` 字段 | ✅ 借鉴，防编辑冲突 |
| 编辑历史 | ✅ JSONB 最近10条 | ✅ 借鉴 |
| 软删除 | ❌ 硬删 | ✅ `is_deleted`（Reddit 风格） |
| @提及 | ✅ EventBus 异步 | 🔲 Phase 2 |
| Reactions | ✅ 7种 emoji | 简化为点赞（`blog_comment_likes`） |
| 深度限制 | 环境变量（默认5） | 环境变量（默认不限，可配） |
| 权限 | ACL VIEWER/COMMENTER/EDITOR/ADMIN | 简化：未登录只读，登录可评，admin 可删任意 |
| 级联删除 | `parent_reply_id` CASCADE | 同 |
| Quote 保留 | `quote_reply_id` SET NULL | 同，`quote_id` SET NULL |
| 冗余 author_name | ❌（需 JOIN users） | ✅ 冗余存（避免 JOIN 主 DB） |

---

### API 设计

```
GET  /api/blogs/articles/{id}/comments          # 获取评论树（分页，flat list，前端建树）
POST /api/blogs/articles/{id}/comments          # 发评论（需登录）
PUT  /api/blogs/comments/{comment_id}           # 编辑（需本人 + version）
DELETE /api/blogs/comments/{comment_id}         # 软删除（本人或 admin）
POST /api/blogs/comments/{comment_id}/like      # 点赞 toggle
```

---

### 前端渲染策略：Flat List → 前端建树

从 Lichess 借鉴的核心思路：**后端返回 flat list，前端按 `parent_id` 递归建树**。

```typescript
// 后端返回 flat array
[
  { id: "A", parent_id: null, content: "..." },
  { id: "B", parent_id: "A",  content: "..." },
  { id: "C", parent_id: "B",  content: "..." },
]

// 前端建树
function buildTree(comments) {
  const map = {};
  const roots = [];
  for (const c of comments) {
    map[c.id] = { ...c, children: [] };
  }
  for (const c of comments) {
    if (c.parent_id) map[c.parent_id].children.push(map[c.id]);
    else roots.push(map[c.id]);
  }
  return roots;
}
```

优点：后端查询简单（单次 SELECT），前端渲染灵活（折叠、缩进、懒加载子评论）。

---

### 软删除渲染（Reddit 风格）

```
[已删除的评论]        ← is_deleted=true，不显示 content 和 author
    └── 我回复的内容   ← 子评论仍可见
```

后端查询时 `is_deleted=true` 的评论仍返回，但只返回 `{ id, parent_id, is_deleted: true }`，不返回 content/author。

---

### 建表方式

沿用项目惯例：**写进 `main.py` 的 `_init_blog_db()`**，Railway 部署时自动建表。

```python
# Step N: Create blog_comments and blog_comment_likes tables
conn.execute(text("""
    CREATE TABLE IF NOT EXISTS blog_comments (
        ...
    );
    CREATE TABLE IF NOT EXISTS blog_comment_likes (
        ...
    );
"""))
```

---

## 三、开发优先级

**Phase 1（MVP）**：
- [x] `blog_comments` 表（含软删除、乐观锁、edit_history）
- [x] 根评论 + 无限嵌套回复（`parent_id`）
- [x] 点赞（`blog_comment_likes`）
- [x] 权限：未登录只读，登录可 CRUD 自己的，admin 可删任意
- [x] 前端 flat → tree 渲染，缩进展示嵌套

**Phase 2**：
- [ ] @提及 + 通知
- [ ] Quote 引用显示
- [ ] 评论数实时更新（WebSocket 或 SSE）
- [ ] 举报功能
