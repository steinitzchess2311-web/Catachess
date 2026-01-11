# Workspace 后端完整设计文档

## 0. 核心约束

### 设计原则

1. **后端是唯一真相源（Source of Truth）**
   - 路径树、权限、版本、PGN 分章、变体层级，都由后端定义与校验
   - 前端只是渲染层，不做业务逻辑

2. **大对象外置存储**
   - PGN 大对象进 R2（Cloudflare R2 对象存储）
   - 数据库只存引用 key + 元数据 + ACL + 索引

3. **事件驱动架构**
   - 所有操作都产生事件（用于前端实时更新、协作、审计、通知、回滚）
   - 事件是系统的"神经网络"

4. **协作编辑支持**
   - Study 编辑模型支持多用户协作
   - 至少支持乐观锁（version/etag）
   - 未来可升级到 CRDT，但现在先不把自己绑死

---

## 1. 全功能清单

### A. Workspace / Folder / Study 三类对象

#### 节点类型定义

```python
from enum import Enum

class NodeType(str, Enum):
    WORKSPACE = "workspace"  # 顶层工作空间
    FOLDER = "folder"        # 文件夹（可无限嵌套）
    STUDY = "study"          # 学习项目（叶子节点）
    # 未来可扩展：file, board, snippet 等
```

#### A1. 节点基础能力

| 操作 | 说明 | 权限要求 |
|------|------|----------|
| **创建** | 创建 workspace / folder / study | owner/admin |
| **重命名** | 修改节点标题 | editor 及以上 |
| **删除** | 软删除 → 回收站 | owner/admin |
| **永久删除** | 从回收站彻底删除 | owner |
| **移动** | 改变 parent + 更新路径 | editor 及以上 |
| **复制** | Deep copy（可选是否复制权限） | editor 及以上 |
| **导出** | 导出 study PGN / folder zip | viewer 及以上 |
| **退出** | 从 shared 中移除自己 | 自己 |
| **搜索** | 按标题、标签、内容搜索 | viewer 及以上 |

#### A2. 路径树结构（核心创新）

**重要：Folder 可以无限嵌套！**

支持的路径结构示例：
```
workspace
├── folder_1
│   ├── study_1
│   ├── folder_1_1
│   │   ├── study_2
│   │   └── folder_1_1_1
│   │       └── study_3
│   └── folder_1_2
│       └── study_4
└── folder_2
    └── study_5
```

完整路径示例：
```
workspace/folder_1/folder_1_1/folder_1_1_1/study_3
```

**路径树特性：**

- **任意层级嵌套**：folder 套 folder，无深度限制（建议前端 UI 限制显示深度）
- **路径持久化**：DB 存 `parent_id` + `materialized_path`（如 `/ws1/f1/f2/`）或使用 closure table
- **自动规整化**：支持桌面拖拽位置 + 自动整理布局
- **Layout 元数据**：后端保存 `x`, `y`, `z`, `group`, `viewMode`
- **Auto-arrange**：后端计算自动排列结果，前端只负责渲染
- **视图模式**：支持"列表视图"（list）和"卡片视图"（grid）
- **排序与过滤**：后端提供排序字段、过滤条件、分页 cursor

#### A3. 分享（Share）与协作

**分享能力：**

- **workspace/folder/study 都可 share**（任意节点均可分享）
- **邀请方式**：
  - 邀请指定用户（email / user_id）
  - 生成可撤销链接（可选 password、expiry）

**权限层级：**

```python
class Permission(str, Enum):
    OWNER = "owner"          # 全权限（删除、转移所有权）
    ADMIN = "admin"          # 管理成员、改设置
    EDITOR = "editor"        # 编辑内容
    COMMENTER = "commenter"  # 仅评论讨论
    VIEWER = "viewer"        # 只读
```

**权限继承规则：**

- Folder 的权限**可选择**"继承给子节点"或"断开继承"
- Share 时可选"只分享这个节点"或"递归分享子树"
- **规则校验（后端硬校验）**：
  - `viewer` 不可写
  - `editor` 不可改 ACL（除非是 `admin`）
  - 退出 share 后：只移除自己在 share 列表中的记录

**"Shared with me" 视图：**

- 支持按对象类型过滤（只看 study / folder / workspace）
- 支持按分享者过滤
- 支持隐藏/退出

---

### B. Study（核心对标 Lichess Study）

Study 是最小研究单位：**章节（chapter）+ PGN + 变体树 + 注释 + 版本**

#### B1. Study 基础

**创建与元信息：**

```python
class StudyMetadata:
    title: str
    description: str | None
    tags: list[str]  # 开局、主题、来源、难度
    visibility: Visibility  # private/shared/public(future)
    initial_fen: str | None  # 可选起始局面
```

**成员与权限：** 复用 share ACL 系统

#### B2. PGN 导入与自动切割（chapter_detector）

**导入流程：**

1. 上传/粘贴 PGN（可能包含多盘棋）
2. 解析规则：
   - 以 `[Event "..."]`、`[Site "..."]` 等 **headers 组**切分为"章节"
   - 章节 title 优先级：
     1. `[Event "..."]` / `[Site "..."]` 组合
     2. PGN 自带 `Chapter` 自定义 tag（可支持）
     3. Fallback：`Game 1`, `Game 2`, ...

**64 章节限制策略（创新点）：**

- **≤ 64 章节**：直接导入到一个 study
- **> 64 章节**：
  1. 自动创建 folder（用户提供 `base_name`）
  2. 自动创建 study 分片：`${base_name}_1`, `${base_name}_2`, ...
  3. 每个 study 最多 64 章节

**导入报告：**

```python
class ImportReport:
    success_count: int
    failed_count: int
    skipped: list[SkipReason]
    created_studies: list[str]  # study_ids
    created_folder: str | None  # folder_id if split
```

#### B3. PGN 清洗与复制（创新功能：pgn_cleaner）

**核心功能："从某一步复制 PGN"**

```python
def clip_pgn_from_move(
    chapter_id: str,
    move_path: str,  # 例如 "main.12.var2.3"
) -> str:
    """
    输入：chapter_id + 指定 move_path（主线或某条分支上的节点）
    输出：一个 PGN 文本

    规则：
    1. 自动排除这步之前的变化：只保留 mainline 到该步的主变轨迹
    2. 保留该步之后的所有分支：从该步起，所有 variations 都保留
    """
```

**另外两个导出模式：**

| 模式 | 说明 | 用途 |
|------|------|------|
| `no_comment_pgn` | 保留分支但去掉 comment | 适合分享/比赛 |
| `raw_pgn` | 只保留主线（mainline only） | 简洁查看 |

#### B4. 变体管理（Variation Hierarchy）

**数据模型：**

```python
class Variation:
    """每条变体分支的元数据"""
    variation_id: str
    priority: Priority  # main/secondary/draft
    rank: int           # 整数等级：0=主变，1=次变，2=备选...
    pinned: bool        # 固定在前端展示
    visibility: Visibility  # private/shared
```

**操作：**

- `promote_variation`：提升为主变
- `demote_variation`：降级
- `reorder_siblings`：同级分支排序
- `merge_variation`：合并分支（可选高级功能）

#### B5. 编辑能力（原子操作）

Study 编辑需要最小原子操作（后端定义动作边界）：

```python
# 章节操作
set_chapter_title(chapter_id, title)
set_fen_root(chapter_id, fen)

# 棋步操作
add_move(chapter_id, move_path, san)
delete_move(chapter_id, move_path)
add_variation(chapter_id, parent_move_path, san)
close_variation(chapter_id, variation_path)

# 注释操作（棋步注释，不是讨论）
add_move_annotation(chapter_id, move_path, annotation)
delete_move_annotation(chapter_id, move_path)
edit_move_annotation(chapter_id, move_path, annotation)
set_nag(chapter_id, move_path, nag)  # !!, !?, ?, etc.

# 撤销/重做
undo(study_id, user_id)
redo(study_id, user_id)
```

**Undo/Redo 策略：**

- 服务端基于事件流提供 **per-user undo 栈**
- 先做 study 内 undo（不跨 study）

#### B6. 导出功能

| 导出类型 | 说明 | 产物 |
|----------|------|------|
| 单章节 PGN | 导出一个 chapter | `.pgn` 文件 |
| 整个 study | 合并所有 chapters | `.pgn` 或 `.zip`（每章节单独文件） |
| Folder/Workspace | 递归导出子树 | `.zip`（包含所有 study） |

**大文件导出：** 走异步任务（job），返回 `job_id`，前端轮询/订阅完成事件

---

### C. 权限与删除

#### C1. 权限模型（统一 ACL）

**对象级 ACL：** `workspace` / `folder` / `study` 都使用同一套权限模型

**权限继承：**

```python
class ACLInheritance:
    """ACL 继承规则"""
    inherit_to_children: bool  # 是否继承给子节点
    recursive_share: bool      # Share 时是否递归分享子树
```

**规则校验（后端硬校验）：**

- `viewer` 不可写
- `editor` 不可改 ACL（除非 `admin`）
- 退出 share 后：只移除自己在 share 列表中的记录

#### C2. 删除模型

| 删除类型 | 行为 | 可恢复性 |
|----------|------|----------|
| **软删除** | 进入 trash | ✅ 可恢复 |
| **永久删除** | 从 trash 彻底删除 | ❌ 不可恢复 |

**删除共享对象时：**

- `owner` 删除 = 真删除/软删除（整个对象）
- 非 `owner` 删除 = "退出"或"从我的列表隐藏"

**Trash 清理：** 支持定期清理（30 天）或手动永久删除

---

### D. 搜索 & 索引

**两级搜索：**

1. **元数据搜索（DB）**：
   - 字段：`title`、`tags`、`owner`、`shared_by`、`updated_at`
   - 技术：Postgres 直接查询

2. **内容搜索（索引）**：
   - 字段：`chapter title`、`move annotation`、`discussion comment`、可选 PGN SAN/UCI 文本片段
   - 技术：早期用 Postgres `tsvector`（够用且快），后期可换 Elasticsearch

---

### E. 用户评论与讨论系统（新增核心功能）

#### E1. 双层评论模型

**为什么需要两层？**

区分**专业注释**与**用户交流**：

| 类型 | Move Annotation（棋步注释） | Discussion（对象讨论） |
|------|---------------------------|---------------------|
| **针对** | 具体棋步 | Workspace/Folder/Study 整体 |
| **内容** | 专业技术分析（?!, !!, ?, ! 等 NAG + 文字） | 用户交流、提问、建议 |
| **导出** | ✅ 随 PGN 一起导出 | ❌ 不导出（独立系统） |
| **权限** | `editor` 及以上 | `commenter` 及以上 |
| **存储** | 存在 variation tree 中 | 独立的 discussions 表 |

#### E2. 讨论功能完整清单

**创建讨论主题（Thread）：**

```python
class DiscussionThread:
    thread_id: str
    target_id: str  # workspace_id / folder_id / study_id
    target_type: NodeType
    author_id: str
    title: str
    content: str  # Markdown 格式
    thread_type: ThreadType  # question/suggestion/note
    pinned: bool
    resolved: bool  # 针对 question 类型
    created_at: datetime
    updated_at: datetime
```

**回复与线程：**

```python
class DiscussionReply:
    reply_id: str
    thread_id: str
    parent_reply_id: str | None  # 支持多层嵌套回复
    author_id: str
    content: str  # Markdown 格式
    quote_reply_id: str | None  # 引用回复
    edited: bool
    edit_history: list[EditRecord]  # 保留编辑历史
    created_at: datetime
    updated_at: datetime
```

**嵌套层级限制：** 建议限制 3-5 层，防止过深嵌套影响 UI

**富文本支持：**

- ✅ Markdown 格式
- ✅ 代码高亮（PGN/FEN 片段）
- ✅ 棋盘位置引用（FEN snapshot）
- ✅ 棋步引用（链接到具体 chapter + move）

**互动功能：**

```python
class Reaction:
    """点赞/反应"""
    reaction_id: str
    target_id: str  # thread_id or reply_id
    user_id: str
    emoji: str  # 👍, ❤️, 🎯, etc.
    created_at: datetime
```

- 点赞/反应（👍 ❤️ 🎯 等）
- @提及用户（触发通知）
- 标记为"已解决"（针对 question 类型）

**权限控制：**

| 权限 | 能力 |
|------|------|
| `commenter` | 创建讨论、回复、点赞 |
| `editor` | 编辑任何讨论 |
| `admin`/`owner` | 删除、pin、标记已解决 |

#### E3. 讨论事件

```python
# 讨论主题
discussion.thread.created
discussion.thread.updated
discussion.thread.deleted
discussion.thread.pinned
discussion.thread.resolved
discussion.thread.reopened

# 回复
discussion.reply.added
discussion.reply.edited
discussion.reply.deleted

# 互动
discussion.reaction.added
discussion.reaction.removed
discussion.mention  # @提及用户
```

---

### F. 通知系统（全新完整设计）

#### F1. 通知类型

**协作通知：**

- 被邀请到 workspace/folder/study
- 权限变更（提升为 editor、降为 viewer 等）
- 被移除访问权限

**内容通知：**

- Study 被更新（有新 chapter、有新变体等）
- 关注的 workspace 有新内容

**讨论通知：**

- 被 @提及
- 自己的讨论有新回复
- 参与的讨论有更新
- 提出的问题被标记为"已解决"

**系统通知：**

- 导出任务完成
- 导入任务完成/失败
- 分享链接即将过期
- Trash 清理提醒

#### F2. 通知渠道

```python
class NotificationChannel(str, Enum):
    IN_APP = "in_app"    # 站内通知（必须）
    EMAIL = "email"      # 邮件通知（可选）
    PUSH = "push"        # 推送通知（未来）
```

**站内通知（必须）：**

- 实时 WebSocket 推送
- 未读计数
- 通知中心（分类、分页、标记已读）

**邮件通知（可选）：**

- 用户可配置哪些类型发邮件
- 支持批量摘要（每日/每周）
- 紧急通知立即发送

**推送通知（未来）：**

- 浏览器 push notification
- 移动端推送

#### F3. 通知偏好设置

```python
class NotificationPreference:
    user_id: str
    event_type: str  # "discussion.mention", "study.updated", etc.
    enabled: bool
    channels: list[NotificationChannel]
    digest_frequency: DigestFrequency | None  # daily/weekly/realtime
    quiet_hours_start: time | None
    quiet_hours_end: time | None
    muted_objects: list[str]  # 静音的对象 ID
```

**用户可配置：**

- 哪些事件触发通知
- 哪些对象的通知（关注/静音）
- 通知渠道偏好（站内/邮件/推送）
- 勿扰时段

---

### G. 协作与实时状态（新增）

#### G1. 在线状态（Presence）

```python
class PresenceSession:
    session_id: str
    user_id: str
    study_id: str  # 当前查看的 study
    chapter_id: str | None  # 当前查看的 chapter
    move_path: str | None  # 光标位置（哪步棋）
    status: PresenceStatus  # active/idle/away
    last_heartbeat: datetime
    cursor_position: CursorPosition | None
```

**在线状态显示：**

- 显示谁在查看/编辑同一个 study
- 显示用户光标位置（在哪个 chapter、哪步棋）
- 显示用户活跃状态（`typing`、`idle`、`away`）

**心跳机制：**

- 30 秒无活动 = `idle`
- 5 分钟无活动 = `away`
- 心跳超时后自动清理会话

#### G2. 协作冲突处理

**乐观锁（etag/version）：**

```python
class OptimisticLock:
    """
    每次编辑带版本号
    冲突时返回 409 + 最新版本
    前端提示用户刷新或合并
    """
    version: int
    etag: str
    last_modified: datetime
```

**变体锁（可选高级功能）：**

- 用户正在编辑某条变体时，其他人看到"锁定中"
- 编辑完成或超时后自动释放

#### G3. 活动流（Activity Log）

```python
class ActivityRecord:
    activity_id: str
    actor_id: str
    target_id: str
    target_type: NodeType
    action: str  # "created", "updated", "deleted", etc.
    details: dict  # 操作详情
    timestamp: datetime
```

**记录所有用户操作：**

- 谁在什么时候做了什么
- 用于审计、回滚、统计

**显示：**

- Workspace/Study 级别的"最近活动"
- 用户个人的操作历史

**过滤：**

- 按用户、按操作类型、按时间范围

---

### H. 版本历史与回滚（新增详细设计）

#### H1. 自动版本快照

```python
class StudyVersion:
    version_id: str
    study_id: str
    version_number: int  # 单调递增
    created_by: str
    created_at: datetime
    change_summary: str  # 基于事件生成的摘要
    snapshot_key: str  # R2 中的快照内容
    parent_version: int | None
    is_rollback: bool  # 是否是回滚产生的版本
```

**Study 每次编辑自动保存版本：**

- 版本号（单调递增）
- 时间戳
- 操作者
- 变更摘要（基于事件）

**快照策略：**

1. **关键操作立即快照**：导入、删除 chapter、promote variation
2. **小编辑累积后定期快照**：如 10 次操作或 5 分钟
3. **手动创建快照**："保存检查点"

#### H2. 版本对比

```python
class VersionDiff:
    """版本对比结果"""
    added_moves: list[Move]
    deleted_moves: list[Move]
    modified_moves: list[Move]
    added_annotations: list[Annotation]
    deleted_annotations: list[Annotation]
    modified_annotations: list[Annotation]
    added_chapters: list[Chapter]
    deleted_chapters: list[Chapter]
```

**比较两个版本：**

- 显示增删改的 moves
- 显示增删改的 annotations
- 显示增删改的 chapters
- 可视化展示（diff view）

#### H3. 回滚机制

**回滚到指定版本：**

- 创建新版本（不真删历史）
- 保留回滚记录（"回滚到版本 X"）

**选择性回滚：**

- 只回滚某个 chapter
- 只回滚某条 variation

---

### I. 事件系统（前端 Hooks - 扩展版）

#### I1. 事件总原则

**每个写操作产生事件：**

```python
class Event:
    event_id: str
    type: str  # "workspace.created", "study.updated", etc.
    actor_id: str
    target_id: str
    target_type: NodeType
    timestamp: datetime
    version: int  # 对象版本号
    payload: dict  # 最小必要 diff
```

**事件投递：**

- **WebSocket**（实时协作）
- **也写入 DB**（审计、回放、undo、通知）

#### I2. 必备事件列表（完整）

**节点操作：**

```
workspace.created / updated / deleted / moved
folder.created / renamed / deleted / moved
study.created / updated / deleted / moved
layout.updated（拖拽位置、auto-arrange 后位置）
```

**权限操作：**

```
acl.shared / acl.revoked / acl.role_changed / acl.link_created
acl.inherited / acl.inheritance_broken
```

**Study 内容：**

```
study.chapter.imported / split_to_folder（>64 自动拆分）
study.chapter.created / renamed / deleted / reordered
study.move.added / move.deleted / variation.promoted / variation.reordered
study.move_annotation.added / updated / deleted（棋步注释）
study.snapshot.created（版本快照）
study.rollback（回滚）
```

**讨论系统：**

```
discussion.thread.created / updated / deleted / pinned / resolved
discussion.reply.added / edited / deleted
discussion.reaction.added / removed
discussion.mention（@提及）
```

**导出系统：**

```
pgn.export.requested / export.completed / export.failed
pgn.clipboard.generated（复制清洗后的 pgn 生成完成）
```

**协作状态：**

```
presence.user_joined / user_left / user_idle / user_active
presence.cursor_moved（光标位置更新）
```

**通知系统：**

```
notification.created / read / dismissed / bulk_read
```

**前端"钩子要求"**：前端只需要订阅这些事件，就能刷新 UI，而不是自己猜状态。

---

## 2. 数据存储设计

### 2.1 R2 存什么

Cloudflare R2 对象存储（S3 兼容）：

```
r2://workspace-storage/
├── raw/                           # 原始导入 PGN（可选保留）
│   └── {upload_id}.pgn
├── chapters/                      # 章节级 PGN（标准化后）
│   └── {chapter_id}.pgn
├── exports/                       # 导出产物
│   ├── {job_id}.pgn
│   └── {job_id}.zip
└── snapshots/                     # 版本快照
    └── {study_id}/
        └── {version}.json
```

**可选：** 变体树 JSON 快照（若你不想完全存在 DB）

### 2.2 DB 存什么（Postgres）

核心数据表：

| 表名 | 说明 |
|------|------|
| `users` | 用户、成员关系 |
| `nodes` | Node 树（workspace/folder/study） |
| `studies` | Study 元信息 |
| `chapters` | Chapter 元信息 + 指向 R2 key |
| `variations` | 变体树数据（建议 DB 存树结构） |
| `move_annotations` | 棋步注释（NAG + 文字分析） |
| `discussions` | 讨论主题表 |
| `replies` | 回复表（支持嵌套） |
| `reactions` | 反应/点赞表 |
| `notifications` | 通知表 |
| `notification_preferences` | 通知偏好设置表 |
| `acl` | 权限表：对象-用户-角色 |
| `share_links` | 分享链接表：token/expiry/password_hash |
| `events` | 事件流表：用于订阅/回放/undo |
| `export_jobs` | 导出任务表：状态机与产物 key |
| `search_index` | 搜索索引表/tsvector |
| `presence_sessions` | 在线状态会话表 |
| `study_versions` | Study 版本历史表 |
| `version_snapshots` | 版本快照元数据表（内容在 R2） |
| `activity_log` | 活动日志表 |

---

## 3. API 设计（后端接口骨架）

### 3.1 REST Endpoints

**节点操作：**

```python
POST   /workspaces                      # 创建 workspace
GET    /workspaces/{id}                 # 获取 workspace
PUT    /workspaces/{id}                 # 更新 workspace

POST   /folders                         # 创建 folder
GET    /folders/{id}                    # 获取 folder
PUT    /folders/{id}                    # 更新 folder

GET    /nodes/tree?workspace_id={id}   # 获取节点树
POST   /nodes/move                      # 移动节点
POST   /nodes/copy                      # 复制节点
DELETE /nodes/{id}                      # 删除节点（软删除）

POST   /share                           # 分享节点
DELETE /share                           # 取消分享
GET    /shared-with-me                  # 获取分享给我的列表
```

**Study 操作：**

```python
POST   /studies                         # 创建 study
GET    /studies/{id}                    # 获取 study
PUT    /studies/{id}                    # 更新 study

POST   /studies/{id}/import-pgn         # 导入 PGN（含 chapter_detector + 64 split）
POST   /studies/{id}/pgn/clip           # PGN Cleaner（从某步复制）
POST   /studies/{id}/export             # 导出 study

GET    /studies/{id}/versions           # 版本历史
GET    /studies/{id}/versions/{v}/diff  # 版本对比
POST   /studies/{id}/rollback           # 回滚
```

**讨论系统：**

```python
POST   /discussions                     # 创建讨论主题
GET    /discussions?target_id={id}      # 获取讨论列表
PUT    /discussions/{thread_id}         # 更新讨论
DELETE /discussions/{thread_id}         # 删除讨论
PATCH  /discussions/{thread_id}/resolve # 标记已解决

POST   /discussions/{thread_id}/replies # 回复
PUT    /replies/{reply_id}              # 编辑回复
DELETE /replies/{reply_id}              # 删除回复

POST   /reactions                       # 添加反应
DELETE /reactions/{reaction_id}         # 删除反应
```

**通知系统：**

```python
GET    /notifications                   # 获取通知列表
POST   /notifications/read              # 标记已读
POST   /notifications/bulk-read         # 批量标记已读
DELETE /notifications/{id}              # 删除通知

GET    /notifications/preferences       # 获取偏好设置
PUT    /notifications/preferences       # 更新偏好设置
```

**协作系统：**

```python
GET    /presence/{study_id}             # 获取在线用户
POST   /presence/heartbeat              # 心跳
```

### 3.2 WebSocket Endpoints

```python
WS /events?scope=workspace:{id}         # 订阅 workspace 事件
WS /events?scope=study:{id}             # 订阅 study 事件
WS /presence?study_id={id}              # 实时状态同步
```

---

## 4. 文件架构（详细到每个文件）

### 目录结构

```
workspace/
├── README.md                                           # 模块总说明与红线
├── pyproject.toml                                      # 依赖与工具配置
├── __init__.py                                         # 包入口
│
├── api/                                                # API 层
│   ├── __init__.py
│   ├── router.py                                       # 路由聚合
│   ├── deps.py                                         # 依赖注入（认证、权限、db session）
│   ├── schemas/                                        # API Schema（Pydantic）
│   │   ├── __init__.py
│   │   ├── node.py                                     # workspace/folder/study 节点 schema
│   │   ├── study.py                                    # study/chapter/move/annotation schema
│   │   ├── share.py                                    # share/ACL/link schema
│   │   ├── export.py                                   # 导出任务 schema
│   │   ├── search.py                                   # 搜索请求响应 schema
│   │   ├── discussion.py                               # 讨论/回复/反应 schema
│   │   ├── notification.py                             # 通知 schema
│   │   ├── presence.py                                 # 在线状态 schema
│   │   └── version.py                                  # 版本历史 schema
│   ├── endpoints/                                      # REST Endpoints
│   │   ├── __init__.py
│   │   ├── nodes.py                                    # 节点树 CRUD/move/copy/delete/trash
│   │   ├── workspaces.py                               # workspace 创建/设置/列表
│   │   ├── studies.py                                  # study 创建/设置/导入/编辑
│   │   ├── shares.py                                   # 分享、权限、shared-with-me
│   │   ├── exports.py                                  # 导出任务创建、查询、下载链接
│   │   ├── search.py                                   # 搜索与过滤接口
│   │   ├── discussions.py                              # 讨论主题/回复/反应/解决
│   │   ├── notifications.py                            # 通知列表/已读/偏好设置
│   │   ├── versions.py                                 # 版本历史/对比/回滚
│   │   └── activity.py                                 # 活动日志查询
│   └── websocket/                                      # WebSocket
│       ├── __init__.py
│       ├── events_ws.py                                # 事件订阅 WS
│       └── presence_ws.py                              # 在线成员/协作状态 WS
│
├── domain/                                             # 领域层（业务逻辑）
│   ├── __init__.py
│   ├── models/                                         # 领域模型
│   │   ├── __init__.py
│   │   ├── node.py                                     # Node 聚合根（workspace/folder/study）
│   │   ├── study.py                                    # Study 聚合根（章节、变体、元信息）
│   │   ├── chapter.py                                  # Chapter 模型（指向 PGN 内容）
│   │   ├── variation.py                                # 变体树节点与分支元数据（rank/priority）
│   │   ├── move_annotation.py                          # 棋步注释模型（NAG + 文字分析）
│   │   ├── discussion.py                               # 讨论主题与回复模型
│   │   ├── reaction.py                                 # 反应/点赞模型
│   │   ├── notification.py                             # 通知模型
│   │   ├── acl.py                                      # ACL 与角色模型
│   │   ├── event.py                                    # 事件模型（持久化）
│   │   ├── export_job.py                               # 导出任务模型（状态机）
│   │   ├── presence.py                                 # 在线状态模型
│   │   ├── version.py                                  # 版本快照模型
│   │   └── activity.py                                 # 活动记录模型
│   ├── services/                                       # 领域服务
│   │   ├── __init__.py
│   │   ├── node_service.py                             # 节点树操作（move/copy/delete/restore）
│   │   ├── workspace_service.py                        # workspace 业务（layout/arrange/view）
│   │   ├── share_service.py                            # 分享与权限（invite/link/revoke/role）
│   │   ├── study_service.py                            # study 业务（章节、编辑、版本、undo）
│   │   ├── chapter_import_service.py                   # PGN 导入总流程（含自动切割/64 拆分）
│   │   ├── variation_service.py                        # 主变/次变/排序/提升降级
│   │   ├── pgn_clip_service.py                         # 从某步复制清洗 PGN（pgn cleaner）
│   │   ├── export_service.py                           # 导出 job 创建/执行/产物写 R2
│   │   ├── search_service.py                           # 搜索服务（元数据 + 内容索引）
│   │   ├── discussion_service.py                       # 讨论创建/回复/提及/解决
│   │   ├── notification_service.py                     # 通知创建/发送/批量处理
│   │   ├── presence_service.py                         # 在线状态管理/心跳/清理
│   │   ├── version_service.py                          # 版本快照/对比/回滚
│   │   └── activity_service.py                         # 活动日志记录/查询
│   └── policies/                                       # 业务策略
│       ├── __init__.py
│       ├── permissions.py                              # 权限判定规则（viewer/editor/admin）
│       ├── inheritance.py                              # ACL 继承/断开继承规则
│       ├── limits.py                                   # 64 chapters 限制与拆分策略
│       ├── concurrency.py                              # 乐观锁/version/etag 规则
│       └── notification_rules.py                       # 通知触发规则与过滤
│
├── pgn/                                                # PGN 处理工具
│   ├── __init__.py
│   ├── parser/                                         # PGN 解析
│   │   ├── __init__.py
│   │   ├── split_games.py                              # 按 headers([]) 切分多盘棋
│   │   ├── normalize.py                                # 标准化（换行/编码/空白）
│   │   └── errors.py                                   # PGN 解析错误与定位信息
│   ├── chapter_detector.py                             # 章节检测与 64 拆分执行器
│   ├── cleaner/                                        # PGN 清洗工具
│   │   ├── __init__.py
│   │   ├── pgn_cleaner.py                              # 从某步复制（去前变体、保后分支）
│   │   ├── no_comment_pgn.py                           # 导出：保留分支但去注释
│   │   ├── raw_pgn.py                                  # 导出：只保留主线
│   │   └── variation_pruner.py                         # 按规则裁剪/保留变体的通用工具
│   ├── serializer/                                     # PGN 序列化
│   │   ├── __init__.py
│   │   ├── to_pgn.py                                   # 变体树/注释/顺序 → PGN 文本
│   │   └── to_tree.py                                  # PGN 文本 → 变体树结构
│   └── tests_vectors/                                  # PGN 测试向量
│       ├── __init__.py
│       ├── sample_multi_game.pgn                       # 多盘棋导入测试样本
│       ├── sample_many_chapters.pgn                    # >64 chapters 拆分测试样本
│       └── sample_variations.pgn                       # 复杂括号变体测试样本
│
├── storage/                                            # 存储层（R2）
│   ├── __init__.py
│   ├── r2_client.py                                    # Cloudflare R2 S3 客户端封装
│   ├── keys.py                                         # R2 key 命名规范生成器
│   ├── presign.py                                      # 预签名上传/下载 URL
│   └── integrity.py                                    # 哈希/etag 校验与去重
│
├── db/                                                 # 数据库层
│   ├── __init__.py
│   ├── session.py                                      # 数据库会话创建与管理
│   ├── migrations/                                     # 数据库迁移脚本
│   │   └── README.md                                   # 迁移规范与执行说明
│   ├── tables/                                         # ORM 表定义
│   │   ├── __init__.py
│   │   ├── nodes.py                                    # 节点表：workspace/folder/study 树结构
│   │   ├── studies.py                                  # study 元信息表
│   │   ├── chapters.py                                 # chapter 表：title/order/r2_key/version
│   │   ├── variations.py                               # 变体树表：parent/next/rank/priority
│   │   ├── move_annotations.py                         # 棋步注释表（NAG + 分析文字）
│   │   ├── discussions.py                              # 讨论主题表
│   │   ├── replies.py                                  # 回复表（支持嵌套）
│   │   ├── reactions.py                                # 反应/点赞表
│   │   ├── notifications.py                            # 通知表
│   │   ├── notification_preferences.py                 # 通知偏好设置表
│   │   ├── acl.py                                      # 权限表：对象-用户-角色
│   │   ├── share_links.py                              # 分享链接表：token/expiry/password_hash
│   │   ├── events.py                                   # 事件流表：用于订阅/回放/undo
│   │   ├── export_jobs.py                              # 导出任务表：状态机与产物 key
│   │   ├── search_index.py                             # 搜索索引表/tsvector
│   │   ├── presence_sessions.py                        # 在线状态会话表
│   │   ├── study_versions.py                           # study 版本历史表
│   │   ├── version_snapshots.py                        # 版本快照元数据表（内容在 R2）
│   │   └── activity_log.py                             # 活动日志表
│   ├── repos/                                          # Repository 层
│   │   ├── __init__.py
│   │   ├── node_repo.py                                # 节点树读写封装
│   │   ├── study_repo.py                               # study/chapter/variation 聚合读写
│   │   ├── discussion_repo.py                          # 讨论/回复/反应读写
│   │   ├── notification_repo.py                        # 通知读写与批量操作
│   │   ├── acl_repo.py                                 # ACL 读写与批量继承
│   │   ├── event_repo.py                               # 事件写入与分页读取
│   │   ├── export_repo.py                              # 导出任务读写
│   │   ├── presence_repo.py                            # 在线状态读写与清理
│   │   ├── version_repo.py                             # 版本历史读写
│   │   ├── activity_repo.py                            # 活动日志读写
│   │   └── search_repo.py                              # 搜索查询封装
│   └── tx.py                                           # 事务封装：确保"写 DB + 写事件"一致性
│
├── events/                                             # 事件系统
│   ├── __init__.py
│   ├── types.py                                        # 事件类型枚举与 payload 规范
│   ├── bus.py                                          # 事件发布总线（写入DB + 推送WS）
│   ├── outbox.py                                       # outbox 模式（避免消息丢失）
│   └── subscribers/                                    # 事件订阅者
│       ├── __init__.py
│       ├── ws_publisher.py                             # WebSocket 推送订阅者
│       ├── notification_creator.py                     # 通知创建订阅者（监听事件自动创建通知）
│       ├── email_sender.py                             # 邮件发送订阅者
│       ├── search_indexer.py                           # 搜索索引更新订阅者
│       ├── activity_logger.py                          # 活动日志订阅者
│       └── audit_logger.py                             # 审计日志订阅者
│
├── collaboration/                                      # 协作模块
│   ├── __init__.py
│   ├── presence_manager.py                             # 在线状态管理器（心跳/超时/清理）
│   ├── cursor_tracker.py                               # 光标位置追踪
│   ├── lock_manager.py                                 # 编辑锁管理器（可选）
│   └── conflict_resolver.py                            # 冲突解决策略（乐观锁处理）
│
├── notifications/                                      # 通知模块
│   ├── __init__.py
│   ├── channels/                                       # 通知渠道
│   │   ├── __init__.py
│   │   ├── in_app.py                                   # 站内通知渠道
│   │   ├── email.py                                    # 邮件通知渠道
│   │   └── push.py                                     # 推送通知渠道（未来）
│   ├── templates/                                      # 通知模板
│   │   ├── __init__.py
│   │   ├── discussion_mention.py                       # @提及通知模板
│   │   ├── share_invite.py                             # 分享邀请通知模板
│   │   ├── export_complete.py                          # 导出完成通知模板
│   │   └── study_update.py                             # study 更新通知模板
│   ├── aggregator.py                                   # 通知聚合器（批量摘要）
│   └── dispatcher.py                                   # 通知分发器（根据偏好选择渠道）
│
├── jobs/                                               # 异步任务
│   ├── __init__.py
│   ├── runner.py                                       # 任务执行器（celery/rq/自研均可替换）
│   ├── export_job.py                                   # 导出任务实现（zip/pgn 产物写 R2）
│   ├── import_job.py                                   # 大 PGN 导入任务（可异步）
│   ├── cleanup_job.py                                  # trash 清理/过期 share link 清理
│   ├── snapshot_job.py                                 # 定期版本快照任务
│   ├── notification_digest_job.py                      # 通知摘要生成任务（每日/每周）
│   └── presence_cleanup_job.py                         # 清理过期在线状态
│
└── tests/                                              # 测试
    ├── __init__.py
    ├── conftest.py                                     # 测试夹具：db/r2 mock/user factory
    ├── test_nodes_tree.py                              # 节点树：create/move/copy/path/arrange
    ├── test_acl_permissions.py                         # 权限：读写/继承/分享链接/撤销
    ├── test_shared_with_me.py                          # shared-with-me 列表与退出/隐藏
    ├── test_study_import_split.py                      # 导入 PGN + 章节检测 + 64 拆分
    ├── test_variation_rank_promote.py                  # 变体等级：主变提升/排序/可见性
    ├── test_pgn_cleaner_clip.py                        # 复制清洗：去前变体保后分支
    ├── test_no_comment_and_raw_export.py               # no_comment / raw 主线导出
    ├── test_export_jobs.py                             # 导出任务：创建/执行/完成事件
    ├── test_search_metadata_and_content.py             # 搜索：标题/章节/内容索引
    ├── test_events_stream.py                           # 事件：写入/订阅/版本递增/回放
    ├── test_concurrency_etag.py                        # 乐观锁：并发编辑冲突处理
    ├── test_discussions.py                             # 讨论：创建/回复/嵌套/@提及/反应
    ├── test_notifications.py                           # 通知：创建/分发/渠道选择/批量处理
    ├── test_presence.py                                # 在线状态：心跳/超时/光标追踪
    ├── test_versions.py                                # 版本：快照/对比/回滚
    ├── test_activity_log.py                            # 活动日志：记录/查询/过滤
    └── test_move_annotations.py                        # 棋步注释：区分于讨论评论的专业注释
```

---

## 5. 模块依赖关系（Import 图）

### 5.1 核心依赖路径

```python
# API 层依赖
api/endpoints/studies.py
  ← domain/services/study_service.py
  ← domain/services/chapter_import_service.py
  ← domain/services/pgn_clip_service.py
  ← domain/models/study.py
  ← domain/policies/permissions.py
  ← db/repos/study_repo.py
  ← events/bus.py
  ← storage/r2_client.py
  ← pgn/parser/split_games.py
  ← pgn/chapter_detector.py
  ← pgn/cleaner/pgn_cleaner.py

api/endpoints/discussions.py
  ← domain/services/discussion_service.py
  ← domain/models/discussion.py
  ← domain/policies/permissions.py
  ← db/repos/discussion_repo.py
  ← events/bus.py

api/endpoints/notifications.py
  ← domain/services/notification_service.py
  ← domain/models/notification.py
  ← db/repos/notification_repo.py
  ← notifications/dispatcher.py

# 领域服务依赖
domain/services/study_service.py
  ← domain/models/study.py
  ← domain/models/chapter.py
  ← domain/models/variation.py
  ← domain/policies/concurrency.py
  ← db/repos/study_repo.py
  ← events/bus.py
  ← storage/r2_client.py

domain/services/chapter_import_service.py
  ← pgn/parser/split_games.py
  ← pgn/chapter_detector.py
  ← pgn/serializer/to_tree.py
  ← domain/services/study_service.py
  ← domain/services/node_service.py
  ← domain/policies/limits.py

domain/services/discussion_service.py
  ← domain/models/discussion.py
  ← domain/models/reaction.py
  ← db/repos/discussion_repo.py
  ← events/bus.py
  ← notifications/dispatcher.py  # 触发 @提及通知

domain/services/notification_service.py
  ← domain/models/notification.py
  ← db/repos/notification_repo.py
  ← notifications/channels/in_app.py
  ← notifications/channels/email.py
  ← notifications/aggregator.py

# 事件系统依赖
events/bus.py
  ← events/types.py
  ← db/repos/event_repo.py
  ← events/subscribers/ws_publisher.py
  ← events/subscribers/notification_creator.py
  ← events/subscribers/search_indexer.py
  ← events/subscribers/activity_logger.py

events/subscribers/notification_creator.py
  ← domain/services/notification_service.py
  ← domain/policies/notification_rules.py

events/subscribers/search_indexer.py
  ← db/repos/search_repo.py

# PGN 处理依赖
pgn/chapter_detector.py
  ← pgn/parser/split_games.py
  ← pgn/parser/normalize.py
  ← domain/policies/limits.py  # 64 章节限制

pgn/cleaner/pgn_cleaner.py
  ← pgn/serializer/to_tree.py
  ← pgn/serializer/to_pgn.py
  ← pgn/cleaner/variation_pruner.py

# 协作系统依赖
collaboration/presence_manager.py
  ← domain/models/presence.py
  ← db/repos/presence_repo.py
  ← events/bus.py

# 通知系统依赖
notifications/dispatcher.py
  ← notifications/channels/in_app.py
  ← notifications/channels/email.py
  ← notifications/channels/push.py
  ← db/repos/notification_repo.py

notifications/channels/email.py
  ← notifications/templates/discussion_mention.py
  ← notifications/templates/share_invite.py
  ← notifications/templates/export_complete.py
```

### 5.2 外部依赖（pyproject.toml）

```toml
[project]
name = "catachess-workspace"
version = "0.1.0"
requires-python = ">=3.11"

dependencies = [
    # Web Framework
    "fastapi>=0.110.0",
    "uvicorn[standard]>=0.27.0",
    "websockets>=12.0",

    # Database
    "sqlalchemy>=2.0.25",
    "alembic>=1.13.1",
    "asyncpg>=0.29.0",  # Postgres async driver

    # Object Storage
    "boto3>=1.34.0",  # S3 compatible (for R2)
    "boto3-stubs[s3]>=1.34.0",

    # Chess/PGN
    "chess>=1.10.0",  # python-chess for PGN parsing

    # Events & Jobs
    "celery>=5.3.6",  # or use rq/arq
    "redis>=5.0.1",

    # Utilities
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "python-multipart>=0.0.6",
    "email-validator>=2.1.0",

    # Markdown & Rich Text
    "markdown>=3.5.0",
    "bleach>=6.1.0",  # HTML sanitization

    # Testing
    "pytest>=7.4.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
    "faker>=22.0.0",
    "httpx>=0.26.0",
]

[project.optional-dependencies]
dev = [
    "mypy>=1.8.0",
    "ruff>=0.1.15",
    "black>=24.1.0",
]
```

---

## 6. 测试要求（5 层测试策略）

### 6.1 单元测试（Unit）

| 测试对象 | 文件 |
|----------|------|
| PGN 分割（headers 切分） | `test_pgn_parser.py` |
| chapter_detector（<=64 / >64） | `test_chapter_detector.py` |
| pgn_cleaner（去前变体、保后分支） | `test_pgn_cleaner_clip.py` |
| variation_rank promote/demote/reorder | `test_variation_rank_promote.py` |
| ACL 权限判定（viewer/editor/admin） | `test_acl_permissions.py` |
| 通知触发规则与过滤 | `test_notification_rules.py` |
| 在线状态心跳与超时 | `test_presence_heartbeat.py` |

### 6.2 集成测试（Integration）

| 测试对象 | 文件 |
|----------|------|
| DB 事务：写节点 + 写事件一致 | `test_db_transaction.py` |
| R2 存取：key 生成、上传、下载、etag 校验 | `test_r2_storage.py` |
| Search：写入索引，查询命中 | `test_search_metadata_and_content.py` |
| 讨论回复嵌套层级限制 | `test_discussions.py` |
| 通知聚合与批量发送 | `test_notifications.py` |

### 6.3 API 测试（Contract）

| 测试对象 | 文件 |
|----------|------|
| endpoints：CRUD、import、clip、export、讨论、通知 | `test_api_*.py` |
| pagination / cursor 规则一致 | `test_api_pagination.py` |
| 错误码一致（403/404/409 等） | `test_api_error_handling.py` |
| WebSocket 连接/断开/重连 | `test_websocket_events.py` |

### 6.4 事件流测试（Realtime Hooks）

| 测试对象 | 文件 |
|----------|------|
| 每个写操作都产生正确事件 type | `test_events_stream.py` |
| event payload 最小 diff 正确 | `test_events_stream.py` |
| 同一对象 version 单调递增 | `test_events_stream.py` |
| WS 订阅 scope 正确隔离 | `test_websocket_isolation.py` |
| 讨论 @提及触发正确事件和通知 | `test_discussion_mention.py` |

### 6.5 协作测试（Concurrency & Realtime）

| 测试对象 | 文件 |
|----------|------|
| 多用户同时编辑：乐观锁冲突处理 | `test_concurrency_etag.py` |
| 在线状态正确同步 | `test_presence.py` |
| 通知不重复发送 | `test_notifications_dedup.py` |
| 版本快照与回滚一致性 | `test_versions.py` |

---

## 7. 落地计划（12 个 Phase）

### Phase 0：定"不可回退"的协议

- 定 `NodeType`、ACL 角色、事件 `types`（写死，不轻易改）
- 定 R2 key 规范（写死）
- 定 chapter 上限策略（64 拆分）与命名规则
- 定通知类型枚举与渠道
- 定讨论主题类型与回复层级限制

### Phase 1：节点树 + 权限（Workspace 最小可用）

- **DB**：`nodes` + `acl` + `events`
- **API**：创建 workspace、创建 folder/study、移动、删除（软删）
- **WS**：订阅 workspace scope 事件
- **测试**：tree + acl + events_stream

### Phase 2：Study 导入（chapter_detector 完整落地）

- PGN `split_games`
- `chapter_detector`（<=64 / >64 创建 folder + studies）
- **R2**：写入 chapter pgn
- 导入报告 + 事件：`chapter.imported` / `split_to_folder`
- **测试**：`import_split`

### Phase 3：变体树编辑模型（对标 study 编辑）

- PGN → tree（`to_tree`）
- tree → PGN（`to_pgn`）
- 支持 `promote`/`reorder`/`visibility`
- 乐观锁 `version`/`etag`（并发编辑 409）
- 区分 `move_annotation`（棋步注释）
- **测试**：`variation` + `concurrency` + `move_annotations`

### Phase 4：pgn_cleaner（核心创新）

- 定 `move_path` 表示（例如 `main.12.var2.3`）
- clip 服务：按规则裁剪 tree，然后序列化成 PGN
- 事件：`pgn.clipboard.generated`
- **测试**：`pgn_cleaner_clip`（大量向量）

### Phase 5：讨论系统（用户评论核心功能）

- **DB**：`discussions` + `replies` + `reactions`
- **API**：创建讨论、回复、嵌套、@提及
- 事件：`discussion.*` 系列
- 搜索索引更新（包含讨论内容）
- **测试**：`discussions`（创建/回复/嵌套/@提及/反应）

### Phase 6：通知系统

- **DB**：`notifications` + `notification_preferences`
- 事件订阅器：自动创建通知
- **API**：通知列表/已读/偏好设置
- 站内通知实时推送（WS）
- **测试**：`notifications`（创建/分发/批量/偏好）

### Phase 7：协作与在线状态

- **DB**：`presence_sessions`
- **API**：心跳、获取在线用户
- **WS**：实时状态同步
- 光标位置追踪（可选）
- **测试**：`presence`（心跳/超时/清理）

### Phase 8：版本历史与回滚

- **DB**：`study_versions` + `version_snapshots`
- 自动快照策略
- **API**：版本列表/对比/回滚
- **R2**：快照内容存储
- **测试**：`versions`（快照/对比/回滚）

### Phase 9：导出与打包

- `export_jobs`：study 导出 PGN；folder/workspace 导出 zip
- job runner（最简先同步，接口保持异步形态）
- **R2** 写产物 + 预签名下载
- **测试**：`export_jobs`

### Phase 10：搜索（查找）

- 元数据搜索先上线（快）
- 内容索引（chapter title + move_annotation + discussion）
- 事件驱动更新索引（写 annotation/discussion 就更新）
- **测试**：`search`

### Phase 11：邮件通知（可选）

- 邮件渠道实现
- 通知模板
- 批量摘要（每日/每周）
- **测试**：email 发送与模板渲染

### Phase 12：活动日志与审计

- **DB**：`activity_log`
- 事件订阅器：自动记录活动
- **API**：活动列表/过滤
- **测试**：`activity_log`

---

## 8. 关键设计决策与权衡

### 8.1 双层评论模型的必要性

**为什么分开 move_annotation 和 discussion？**

| | move_annotation | discussion |
|---|---|---|
| **定位** | Study 内容的一部分 | 围绕 study 的交流 |
| **导出** | ✅ 随 PGN 导出 | ❌ 不导出 |
| **性质** | 专业性强（技术分析） | 社交性强（提问、建议） |
| **权限** | `editor` | `commenter` |

**这种分离保证了：**

- ✅ **PGN 导出的纯净性**（只包含专业注释）
- ✅ **用户交流的灵活性**（不影响 study 内容）
- ✅ **权限的细粒度控制**（commenter 可参与讨论但不能改 study）

### 8.2 通知系统的可扩展性

**为什么设计成多渠道？**

**用户需求多样化：**

- 重要通知希望邮件
- 普通通知站内就好
- 未来可能需要移动推送

**事件驱动架构：**

```
事件产生 → 订阅器创建通知 → 分发器选择渠道
```

- ✅ 添加新渠道不影响现有代码
- ✅ 通知聚合减少打扰

### 8.3 在线状态的性能考虑

**为什么用心跳而非 WebSocket 连接状态？**

**更可靠：**

- WebSocket 断开不一定意味着离开
- 心跳超时才标记为 `idle`/`away`

**更灵活：**

- 可附带光标位置等额外信息
- 可实现 `typing` 等瞬时状态

**性能优化：**

- 批量处理心跳（不是每次都写 DB）
- 定期清理过期会话

### 8.4 版本系统的存储策略

**为什么快照存 R2 而非全在 DB？**

| 优化维度 | 说明 |
|----------|------|
| **空间优化** | Study 可能很大（64 chapters），DB 存元数据，R2 存完整内容 |
| **性能优化** | 版本列表查询快（只查 DB），版本内容按需加载（从 R2） |
| **成本优化** | R2 存储成本低，DB 存储宝贵 |

---

## 9. 未来扩展预留

### 9.1 CRDT 升级路径

| 当前 | 未来 | 预留 |
|------|------|------|
| 乐观锁（version/etag） | CRDT（如 Yjs） | 事件流已包含所有操作，可从事件流重建 CRDT 状态 |

### 9.2 实时协作增强

| 当前 | 未来 |
|------|------|
| 在线状态 + 光标位置 | 实时变体树同步编辑<br>评论实时输入显示<br>视频/语音通话集成 |

**预留：** WebSocket 架构已就位，presence 系统可扩展，事件系统支持任意粒度

### 9.3 AI 辅助功能

| 当前 | 未来 |
|------|------|
| 纯人工内容 | AI 自动生成 move_annotation<br>AI 推荐变体<br>AI 回答讨论问题 |

**预留：**

- `move_annotation` 模型可标记来源（`human`/`ai`）
- `discussion` 可标记为"AI 助手"
- 事件系统可记录 AI 操作

### 9.4 移动端适配

| 当前 | 未来 |
|------|------|
| Web 优先 | 移动 App<br>离线编辑<br>推送通知 |

**预留：**

- API 已 RESTful
- 通知系统已支持推送渠道
- 事件系统支持离线同步

---

## 10. 总结：核心改进点

相比原始计划，新增/改进了：

### 10.1 用户评论功能（核心新增）

- ✅ 双层评论模型：`move_annotation` vs `discussion`
- ✅ 完整讨论系统：主题/回复/嵌套/@提及/反应
- ✅ 富文本支持：Markdown/代码/FEN/棋步引用
- ✅ 权限细化：`commenter` 角色专门用于讨论

### 10.2 通知系统（从简单提及到完整设计）

- ✅ 多种通知类型：协作/内容/讨论/系统
- ✅ 多渠道支持：站内/邮件/推送
- ✅ 用户偏好配置：可控哪些通知、如何接收
- ✅ 通知聚合：减少打扰

### 10.3 协作功能（新增）

- ✅ 在线状态：心跳机制/idle/away
- ✅ 光标追踪：知道其他人在看哪里
- ✅ 冲突处理：乐观锁策略明确
- ✅ 活动日志：完整的操作记录

### 10.4 版本历史（从简单到详细）

- ✅ 自动快照策略：关键操作+定期
- ✅ 版本对比：可视化 diff
- ✅ 选择性回滚：可只回滚部分内容
- ✅ 历史审计：完整操作记录

### 10.5 架构优化

- ✅ 独立模块：`collaboration`/`notifications` 等
- ✅ 更清晰的事件订阅器：`notification_creator`/`search_indexer` 等
- ✅ 更完整的测试覆盖：5 层测试策略
- ✅ 更明确的落地计划：12 个 Phase

---

## 11. 实现优先级建议

### P0（必须）

- **Phase 1-4**：基础节点树 + Study 编辑
- **Phase 5**：讨论系统（用户评论核心需求）
- **Phase 6**：通知系统（讨论的必要配套）

### P1（重要）

- **Phase 7**：在线状态（提升协作体验）
- **Phase 8**：版本历史（安全网）
- **Phase 9**：导出功能（完整闭环）

### P2（增强）

- **Phase 10**：搜索（体验优化）
- **Phase 11**：邮件通知（通知增强）
- **Phase 12**：活动日志（审计需求）

---

**END OF PLAN**

---

## 附录：重要提醒

### A. Folder 无限嵌套

**再次强调：Folder 可以无限嵌套！**

支持的路径深度示例：

```
workspace/f1/f2/f3/f4/f5/f6/f7/study
```

实现时注意：

- ✅ 路径查询优化（materialized path 或 closure table）
- ✅ 前端 UI 限制显示深度（如最多展开 5 层）
- ✅ 移动节点时需要递归更新子树路径
- ✅ 权限继承时需要递归应用

### B. 事件驱动是核心

**所有写操作必须产生事件！**

- ❌ 不要直接修改 DB 后不发事件
- ✅ 使用 `events/bus.py` 统一发布事件
- ✅ 事件是系统的"神经网络"

### C. 双层评论模型是关键

**不要混淆 move_annotation 和 discussion！**

- `move_annotation`：Study 内容的一部分，随 PGN 导出
- `discussion`：用户交流，不导出

这是本系统区别于其他 study 系统的核心创新。
