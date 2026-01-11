# Workspace 模块实施计划

> **设计文档参考**: [claude_plan.md](./claude_plan.md)

## 实施原则

1. **严格按 Phase 顺序推进**：每个 Phase 完成后才进入下一个
2. **Checklist 驱动开发**：所有 ✅ 才算 Phase 完成
3. **测试先行**：每个功能都要有对应测试
4. **事件必发**：所有写操作必须产生事件

---

## Phase 0: 定协议（不可回退）

**目标**: 定义系统核心协议，一旦确定不可轻易修改

### Checklist

- [ ] 定义 `NodeType` 枚举（workspace/folder/study）
- [ ] 定义 ACL 角色枚举（owner/admin/editor/commenter/viewer）
- [ ] 定义所有事件类型（`events/types.py`）
  - [ ] 节点操作事件（workspace.*/folder.*/study.*）
  - [ ] 权限操作事件（acl.*）
  - [ ] Study 内容事件（study.chapter.*/study.move.*）
  - [ ] 讨论事件（discussion.*）
  - [ ] 通知事件（notification.*）
  - [ ] 协作事件（presence.*）
- [ ] 定义 R2 key 命名规范（`storage/keys.py`）
  - [ ] raw/{upload_id}.pgn
  - [ ] chapters/{chapter_id}.pgn
  - [ ] exports/{job_id}.{pgn|zip}
  - [ ] snapshots/{study_id}/{version}.json
- [ ] 定义 64 章节限制策略（`domain/policies/limits.py`）
- [ ] 定义通知类型枚举（`notifications/channels/`）
- [ ] 定义讨论主题类型（question/suggestion/note）
- [ ] 定义回复嵌套层级限制（建议 3-5 层）
- [ ] 编写协议文档（`docs/protocols.md`）

### 完成标准

- ✅ 所有枚举类型已定义并通过 mypy 检查
- ✅ 协议文档已编写并经过 review
- ✅ 所有协议定义文件已提交 git

---

## Phase 1: 节点树 + 权限（Workspace 最小可用）

**目标**: 实现基础节点树结构和权限系统

**参考**: [claude_plan.md § A. Workspace / Folder / Study](./claude_plan.md#a-workspace--folder--study-三类对象)

### 1.1 数据库层

- [ ] 创建 `nodes` 表（ORM 定义）
  - [ ] 支持 parent_id（外键自引用）
  - [ ] 支持 materialized_path（路径字符串）
  - [ ] 支持 layout 元数据（x, y, z, group, viewMode）
  - [ ] 支持软删除（deleted_at）
- [ ] 创建 `acl` 表（对象-用户-角色）
  - [ ] 支持权限继承标记（inherit_to_children）
  - [ ] 支持递归分享标记（recursive_share）
- [ ] 创建 `events` 表（事件流）
  - [ ] 支持 event_id、type、actor_id、target_id
  - [ ] 支持 version（对象版本号）
  - [ ] 支持 payload（JSON）
- [ ] 编写数据库迁移脚本（Alembic）
- [ ] 创建 `node_repo.py`（节点树读写）
- [ ] 创建 `acl_repo.py`（权限读写）
- [ ] 创建 `event_repo.py`（事件写入与读取）

### 1.2 领域层

- [ ] 实现 `domain/models/node.py`（Node 聚合根）
  - [ ] 支持创建、重命名、移动、删除
  - [ ] 支持路径计算（获取完整路径）
- [ ] 实现 `domain/models/acl.py`（ACL 模型）
- [ ] 实现 `domain/services/node_service.py`
  - [ ] create_workspace/folder/study
  - [ ] rename_node
  - [ ] move_node（更新路径 + 子树路径）
  - [ ] delete_node（软删除）
  - [ ] restore_node（从回收站恢复）
- [ ] 实现 `domain/services/share_service.py`
  - [ ] share_node（邀请用户/生成链接）
  - [ ] revoke_share
  - [ ] change_role
- [ ] 实现 `domain/policies/permissions.py`
  - [ ] 权限判定函数（can_read/can_write/can_admin）
  - [ ] 权限继承规则
- [ ] 实现 `events/bus.py`（事件发布总线）
  - [ ] publish_event（写入 DB + 推送订阅者）

### 1.3 API 层

- [ ] 实现 `api/schemas/node.py`（Pydantic schema）
- [ ] 实现 `api/schemas/share.py`
- [ ] 实现 `api/endpoints/workspaces.py`
  - [ ] POST /workspaces（创建 workspace）
  - [ ] GET /workspaces/{id}
  - [ ] PUT /workspaces/{id}
- [ ] 实现 `api/endpoints/folders.py`
  - [ ] POST /folders
  - [ ] GET /folders/{id}
  - [ ] PUT /folders/{id}
- [ ] 实现 `api/endpoints/nodes.py`
  - [ ] GET /nodes/tree（获取节点树）
  - [ ] POST /nodes/move
  - [ ] DELETE /nodes/{id}
- [ ] 实现 `api/endpoints/shares.py`
  - [ ] POST /share
  - [ ] DELETE /share
  - [ ] GET /shared-with-me
- [ ] 实现 `api/deps.py`（依赖注入：认证、权限校验）

### 1.4 WebSocket

- [ ] 实现 `api/websocket/events_ws.py`
  - [ ] 订阅 workspace scope（WS /events?scope=workspace:{id}）
  - [ ] 事件推送给订阅者

### 1.5 测试

- [ ] 单元测试：`test_node_service.py`
  - [ ] 测试创建/重命名/移动/删除
  - [ ] 测试 folder 无限嵌套
  - [ ] 测试路径计算
- [ ] 单元测试：`test_acl_permissions.py`
  - [ ] 测试权限判定（viewer/editor/admin）
  - [ ] 测试权限继承
- [ ] 集成测试：`test_nodes_tree.py`
  - [ ] 测试完整的节点树操作流程
- [ ] 集成测试：`test_events_stream.py`
  - [ ] 测试所有写操作产生事件
  - [ ] 测试 version 单调递增
- [ ] API 测试：`test_api_nodes.py`
  - [ ] 测试所有 REST endpoints
  - [ ] 测试错误处理（403/404/409）
- [ ] WebSocket 测试：`test_websocket_events.py`
  - [ ] 测试 WS 连接/断开
  - [ ] 测试事件推送
  - [ ] 测试 scope 隔离

### 完成标准

- ✅ 所有 checklist 已完成
- ✅ 所有测试通过（覆盖率 > 80%）
- ✅ 可以通过 API 创建 workspace/folder，并查看节点树
- ✅ 可以分享节点并查看"Shared with me"
- ✅ 可以通过 WebSocket 接收事件
- ✅ 代码已提交 git 并 push

---

## Phase 2: Study 导入（chapter_detector）

**目标**: 实现 PGN 导入与自动章节切割

**参考**: [claude_plan.md § B2. PGN 导入](./claude_plan.md#b2-pgn-导入与自动切割chapter_detector)

### 2.1 PGN 解析工具

- [ ] 实现 `pgn/parser/split_games.py`
  - [ ] 按 `[Event "..."]` 等 headers 切分多盘棋
- [ ] 实现 `pgn/parser/normalize.py`
  - [ ] 标准化换行、编码、空白字符
- [ ] 实现 `pgn/parser/errors.py`
  - [ ] 定义解析错误类型
  - [ ] 提供错误定位信息
- [ ] 实现 `pgn/chapter_detector.py`
  - [ ] 检测章节数量
  - [ ] <= 64：返回单 study
  - [ ] > 64：计算需要创建的 study 数量

### 2.2 数据库层

- [ ] 创建 `studies` 表（study 元信息）
- [ ] 创建 `chapters` 表（chapter 元信息 + R2 key）
- [ ] 创建 `study_repo.py`

### 2.3 存储层

- [ ] 实现 `storage/r2_client.py`（S3 兼容客户端）
  - [ ] upload_pgn
  - [ ] download_pgn
- [ ] 实现 `storage/keys.py`（key 生成器）
- [ ] 实现 `storage/integrity.py`（哈希校验）

### 2.4 领域层

- [ ] 实现 `domain/models/study.py`（Study 聚合根）
- [ ] 实现 `domain/models/chapter.py`
- [ ] 实现 `domain/services/chapter_import_service.py`
  - [ ] import_pgn（总流程）
  - [ ] 调用 chapter_detector
  - [ ] <= 64：创建单 study + 写入 R2
  - [ ] > 64：创建 folder + 多个 study
  - [ ] 返回 ImportReport

### 2.5 API 层

- [ ] 实现 `api/schemas/study.py`
- [ ] 实现 `api/endpoints/studies.py`
  - [ ] POST /studies（创建 study）
  - [ ] POST /studies/{id}/import-pgn（导入 PGN）

### 2.6 测试

- [ ] 单元测试：`test_pgn_parser.py`
  - [ ] 测试 split_games
  - [ ] 测试 normalize
- [ ] 单元测试：`test_chapter_detector.py`
  - [ ] 测试 <= 64 场景
  - [ ] 测试 > 64 场景（拆分）
- [ ] 集成测试：`test_study_import_split.py`
  - [ ] 测试完整导入流程
  - [ ] 测试 R2 上传
  - [ ] 测试自动拆分
- [ ] 集成测试：`test_r2_storage.py`
  - [ ] 测试 R2 上传/下载
  - [ ] 测试 key 生成
  - [ ] 测试 etag 校验

### 完成标准

- ✅ 所有 checklist 已完成
- ✅ 所有测试通过（覆盖率 > 80%）
- ✅ 可以导入 <= 64 章节的 PGN
- ✅ 可以导入 > 64 章节的 PGN（自动拆分）
- ✅ PGN 内容已正确存储到 R2
- ✅ 产生正确的事件（study.chapter.imported / split_to_folder）
- ✅ 代码已提交 git 并 push

---

## Phase 3: 变体树编辑模型

**目标**: 实现变体树的编辑、promote/demote、乐观锁

**参考**: [claude_plan.md § B4-B5](./claude_plan.md#b4-变体管理variation-hierarchy)

### 3.1 数据库层

- [x] 创建 `variations` 表（变体树结构）
  - [x] parent_id（父节点）
  - [x] next_id（下一步）
  - [x] rank（等级：0=主变，1=次变...）
  - [x] priority（主变/次变/草稿）
  - [x] pinned、visibility
- [x] 创建 `move_annotations` 表（棋步注释）
  - [x] move_id（关联 variation）
  - [x] nag（?!, !!, ?, !）
  - [x] text（文字分析）
  - [x] author_id

### 3.2 PGN 序列化

- [x] 实现 `pgn/serializer/to_tree.py`
  - [x] PGN 文本 → 变体树结构
  - [x] 解析括号变体
- [x] 实现 `pgn/serializer/to_pgn.py`
  - [x] 变体树 → PGN 文本
  - [x] 保留分支顺序

### 3.3 领域层

- [x] 实现 `domain/models/variation.py`
- [x] 实现 `domain/models/move_annotation.py`
- [x] 实现 `domain/services/variation_service.py`
  - [x] promote_variation（提升为主变）
  - [x] demote_variation
  - [x] reorder_siblings
- [x] 实现 `domain/services/study_service.py`
  - [x] add_move
  - [x] delete_move
  - [x] add_variation
  - [x] add_move_annotation（区分于 discussion）
  - [x] edit_move_annotation
  - [x] delete_move_annotation
  - [x] set_nag
- [x] 实现 `domain/policies/concurrency.py`
  - [x] 乐观锁规则（version/etag）
  - [x] 冲突检测（返回 409）

### 3.4 API 层

- [x] 扩展 `api/endpoints/studies.py`
  - [x] POST /studies/{id}/chapters/{cid}/moves（添加棋步）
  - [x] DELETE /studies/{id}/chapters/{cid}/moves/{move_path}
  - [x] POST /studies/{id}/chapters/{cid}/variations
  - [x] POST /studies/{id}/chapters/{cid}/moves/{move_path}/annotations
  - [x] PUT /studies/{id}/chapters/{cid}/variations/{vid}/promote
- [x] 添加乐观锁支持（If-Match header）

### 3.5 测试

- [x] 单元测试：`test_variation_rank_promote.py`
  - [x] 测试 promote/demote
  - [x] 测试 reorder
- [x] 单元测试：`test_move_annotations.py`
  - [x] 测试添加/编辑/删除注释
  - [x] 测试 NAG 设置
  - [x] 区分 move_annotation 与 discussion
- [x] 集成测试：`test_concurrency_etag.py`
  - [x] 测试并发编辑冲突
  - [x] 测试乐观锁（409 响应）
  - [x] 测试 version 递增
- [x] API 集成测试：`test_api_variation_endpoints.py`（17个测试）
  - [x] 所有5个Phase 3端点的happy path
  - [x] 错误场景（404, 409, 400）
  - [x] If-Match/ETag header支持

### 完成标准

- ✅ 所有 checklist 已完成
- ✅ 所有测试通过（覆盖率 > 80%）
- ✅ 可以添加/删除棋步和变体
- ✅ 可以 promote/demote 变体
- ✅ 可以添加棋步注释（move_annotation）
- ✅ 乐观锁生效（并发冲突返回 409）
- ✅ 产生正确的事件
- ✅ 代码已提交 git 并 push

---

## Phase 4: PGN Cleaner（核心创新）

**目标**: 实现"从某一步复制 PGN"功能

**参考**: [claude_plan.md § B3. PGN 清洗](./claude_plan.md#b3-pgn-清洗与复制创新功能pgn_cleaner)

### 4.1 PGN 清洗工具

- [x] 定义 move_path 表示（如 "main.12.var2.3"）
- [x] 实现 `pgn/cleaner/variation_pruner.py`
  - [x] 按规则裁剪/保留变体的通用工具
- [x] 实现 `pgn/cleaner/pgn_cleaner.py`
  - [x] 输入：chapter_id + move_path
  - [x] 规则1：去前面变体（只保留主线到该步）
  - [x] 规则2：保后面分支（从该步起所有分支）
  - [x] 输出：PGN 文本
- [x] 实现 `pgn/cleaner/no_comment_pgn.py`
  - [x] 保留分支但去掉 comment
- [x] 实现 `pgn/cleaner/raw_pgn.py`
  - [x] 只保留主线（mainline only）

### 4.2 领域层

- [x] 实现 `domain/services/pgn_clip_service.py`
  - [x] clip_pgn_from_move（调用 pgn_cleaner）
  - [x] export_no_comment
  - [x] export_raw

### 4.3 API 层

- [x] 实现 `api/endpoints/studies.py`
  - [x] POST /studies/{id}/pgn/clip（从某步复制）
    - Body: { chapter_id, move_path, mode: "clip" | "no_comment" | "raw" }

### 4.4 测试

- [x] 单元测试：`test_pgn_cleaner_clip.py`
  - [x] 测试去前变体保后分支
  - [x] 测试各种 move_path 输入
  - [x] 测试边界情况（第一步、最后一步）
- [ ] 单元测试：`test_no_comment_and_raw_export.py`
  - [ ] 测试 no_comment 模式
  - [ ] 测试 raw 模式
- [ ] 使用 `pgn/tests_vectors/` 中的样本测试
  - [ ] sample_variations.pgn（复杂括号变体）

### 完成标准

- ✅ 所有 checklist 已完成
- ✅ 所有测试通过（覆盖率 > 80%）
- ✅ 可以从任意棋步复制 PGN
- ✅ 去前变体、保后分支规则正确
- ✅ no_comment 和 raw 模式正确
- ✅ 产生正确的事件（pgn.clipboard.generated）
- ✅ 代码已提交 git 并 push

---

## Phase 5: 讨论系统（用户评论核心功能）

**目标**: 实现双层评论模型与完整讨论系统

**参考**: [claude_plan.md § E. 用户评论](./claude_plan.md#e-用户评论与讨论系统新增核心功能)

### 5.1 数据库层

- [x] 创建 `discussions` 表（讨论主题）
  - [x] target_id + target_type（关联对象）
  - [x] thread_type（question/suggestion/note）
  - [x] pinned、resolved
- [x] 创建 `replies` 表（回复，支持嵌套）
  - [x] parent_reply_id（支持嵌套）
  - [x] quote_reply_id（引用回复）
  - [x] edited + edit_history
- [x] 创建 `reactions` 表（点赞/反应）
  - [x] target_id（thread_id or reply_id）
  - [x] emoji（👍 ❤️ 🎯）
  - [x] 添加嵌套层级限制（数据库约束或应用层）

### 5.2 领域层

- [x] 实现 `domain/models/discussion.py`
  - [x] DiscussionThread
  - [x] DiscussionReply
- [x] 实现 `domain/models/reaction.py`
- [x] 实现 `domain/services/discussion_service.py`
  - [x] create_thread
  - [x] add_reply（检查嵌套层级）
  - [x] edit_reply（保留历史）
  - [x] delete_reply
  - [x] add_reaction
  - [x] remove_reaction
  - [x] resolve_thread / reopen_thread
  - [x] pin_thread
  - [x] parse_mentions（解析 @user）

### 5.3 API 层

- [x] 实现 `api/schemas/discussion.py`
  - [x] ThreadCreate、ReplyCreate、ReactionCreate
  - [x] 支持 Markdown 验证
- [x] 实现 `api/endpoints/discussions.py`
  - [x] POST /discussions（创建讨论）
  - [x] GET /discussions?target_id={id}
  - [x] PUT /discussions/{thread_id}
  - [x] DELETE /discussions/{thread_id}
  - [x] PATCH /discussions/{thread_id}/resolve
  - [x] POST /discussions/{thread_id}/replies
  - [x] PUT /replies/{reply_id}
  - [x] DELETE /replies/{reply_id}
  - [x] POST /reactions
  - [x] DELETE /reactions/{reaction_id}

### 5.4 搜索索引更新

- [x] 扩展 `events/subscribers/search_indexer.py`
  - [x] 监听 discussion.* 事件
  - [x] 更新搜索索引（包含讨论内容）

### 5.5 测试

- [x] 单元测试：`test_discussion_service.py`
  - [x] 测试创建/回复/编辑/删除
  - [x] 测试嵌套层级限制
  - [x] 测试 @提及解析
- [x] 集成测试：`test_discussions.py`
  - [x] 测试完整讨论流程
  - [x] 测试多层嵌套回复
  - [x] 测试 pin/resolve
  - [x] 测试反应/点赞
- [x] 集成测试：`test_discussion_mention.py`
  - [x] 测试 @提及触发事件

### 完成标准

- [x] 所有 checklist 已完成
- [x] 所有测试通过（覆盖率 > 80%）
- [x] 可以创建讨论主题（question/suggestion/note）
- [x] 可以回复并支持嵌套（3-5 层）
- [x] 可以 @提及用户
- [x] 可以添加反应（👍 ❤️ 🎯）
- [x] 可以 pin/resolve 讨论
- [x] 讨论内容已加入搜索索引
- [x] 产生正确的事件（discussion.*）
- [x] **验证双层模型**：move_annotation 与 discussion 互不干扰
- [ ] 代码已提交 git 并 push

---

## Phase 6: 通知系统

**目标**: 实现完整的通知系统（站内通知必须，邮件可选）

**参考**: [claude_plan.md § F. 通知系统](./claude_plan.md#f-通知系统全新完整设计)

### 6.1 数据库层

- [ ] 创建 `notifications` 表
  - [ ] type、target_id、actor_id
  - [ ] read_at（已读时间）
- [ ] 创建 `notification_preferences` 表
  - [ ] event_type + enabled + channels
  - [ ] digest_frequency、quiet_hours
  - [ ] muted_objects

### 6.2 通知渠道

- [ ] 实现 `notifications/channels/in_app.py`（站内通知）
  - [ ] 创建通知记录
  - [ ] 推送到 WebSocket
- [ ] 实现 `notifications/channels/email.py`（邮件通知，可选）
  - [ ] 发送邮件
  - [ ] 使用模板
- [ ] 实现 `notifications/channels/push.py`（推送通知，未来）
  - [ ] 占位实现

### 6.3 通知模板

- [ ] 实现 `notifications/templates/discussion_mention.py`
  - [ ] @提及通知模板
- [ ] 实现 `notifications/templates/share_invite.py`
  - [ ] 分享邀请通知模板
- [ ] 实现 `notifications/templates/export_complete.py`
  - [ ] 导出完成通知模板
- [ ] 实现 `notifications/templates/study_update.py`
  - [ ] study 更新通知模板

### 6.4 通知分发

- [ ] 实现 `notifications/dispatcher.py`
  - [ ] 根据偏好选择渠道
  - [ ] 检查勿扰时段
  - [ ] 检查静音对象
- [ ] 实现 `notifications/aggregator.py`
  - [ ] 通知聚合（批量摘要）

### 6.5 事件订阅器

- [ ] 实现 `events/subscribers/notification_creator.py`
  - [ ] 监听所有需要通知的事件
  - [ ] 自动创建通知
  - [ ] 调用 dispatcher 分发
- [ ] 实现 `domain/policies/notification_rules.py`
  - [ ] 定义哪些事件触发哪些通知
  - [ ] 通知过滤规则

### 6.6 API 层

- [ ] 实现 `api/schemas/notification.py`
- [ ] 实现 `api/endpoints/notifications.py`
  - [ ] GET /notifications（获取通知列表）
  - [ ] POST /notifications/read（标记已读）
  - [ ] POST /notifications/bulk-read（批量已读）
  - [ ] DELETE /notifications/{id}
  - [ ] GET /notifications/preferences
  - [ ] PUT /notifications/preferences

### 6.7 测试

- [ ] 单元测试：`test_notification_rules.py`
  - [ ] 测试通知触发规则
  - [ ] 测试过滤规则
- [ ] 单元测试：`test_notification_dispatcher.py`
  - [ ] 测试渠道选择
  - [ ] 测试勿扰时段
- [ ] 集成测试：`test_notifications.py`
  - [ ] 测试通知创建
  - [ ] 测试通知分发（站内）
  - [ ] 测试批量操作
  - [ ] 测试偏好设置
- [ ] 集成测试：`test_notifications_dedup.py`
  - [ ] 测试通知不重复发送

### 完成标准

- ✅ 所有 checklist 已完成
- ✅ 所有测试通过（覆盖率 > 80%）
- ✅ 站内通知功能正常（必须）
- ✅ 邮件通知功能正常（如果实现）
- ✅ 可以配置通知偏好
- ✅ 可以设置勿扰时段
- ✅ 可以静音特定对象
- ✅ @提及自动触发通知
- ✅ 通知通过 WebSocket 实时推送
- ✅ 产生正确的事件（notification.*）
- ✅ 代码已提交 git 并 push

---

## Phase 7: 协作与在线状态

**目标**: 实现在线状态、心跳、光标追踪

**参考**: [claude_plan.md § G. 协作与实时状态](./claude_plan.md#g-协作与实时状态新增)

### 7.1 数据库层

- [ ] 创建 `presence_sessions` 表
  - [ ] study_id + chapter_id + move_path（光标位置）
  - [ ] status（active/idle/away）
  - [ ] last_heartbeat

### 7.2 协作模块

- [ ] 实现 `collaboration/presence_manager.py`
  - [ ] 心跳处理（更新 last_heartbeat）
  - [ ] 状态更新（active → idle → away）
  - [ ] 超时清理（定期任务）
- [ ] 实现 `collaboration/cursor_tracker.py`
  - [ ] 追踪光标位置
- [ ] 实现 `collaboration/conflict_resolver.py`
  - [ ] 乐观锁冲突解决策略

### 7.3 领域层

- [ ] 实现 `domain/models/presence.py`
- [ ] 实现 `domain/services/presence_service.py`
  - [ ] heartbeat（心跳）
  - [ ] get_online_users
  - [ ] update_cursor_position

### 7.4 API 层

- [ ] 实现 `api/schemas/presence.py`
- [ ] 实现 `api/endpoints/presence.py`
  - [ ] GET /presence/{study_id}（获取在线用户）
  - [ ] POST /presence/heartbeat
- [ ] 实现 `api/websocket/presence_ws.py`
  - [ ] WS /presence?study_id={id}
  - [ ] 实时状态同步

### 7.5 后台任务

- [ ] 实现 `jobs/presence_cleanup_job.py`
  - [ ] 清理过期在线状态（超时会话）

### 7.6 测试

- [ ] 单元测试：`test_presence_heartbeat.py`
  - [ ] 测试心跳更新
  - [ ] 测试状态变化（active → idle → away）
- [ ] 集成测试：`test_presence.py`
  - [ ] 测试在线状态同步
  - [ ] 测试光标位置追踪
  - [ ] 测试超时清理
- [ ] WebSocket 测试：`test_presence_ws.py`
  - [ ] 测试实时状态推送

### 完成标准

- ✅ 所有 checklist 已完成
- ✅ 所有测试通过（覆盖率 > 80%）
- ✅ 可以发送心跳并更新在线状态
- ✅ 可以查看在线用户列表
- ✅ 可以追踪光标位置
- ✅ 状态自动转换（active → idle → away）
- ✅ 超时会话自动清理
- ✅ 通过 WebSocket 实时同步状态
- ✅ 产生正确的事件（presence.*）
- ✅ 代码已提交 git 并 push

---

## Phase 8: 版本历史与回滚

**目标**: 实现自动版本快照、对比、回滚

**参考**: [claude_plan.md § H. 版本历史](./claude_plan.md#h-版本历史与回滚新增详细设计)

### 8.1 数据库层

- [ ] 创建 `study_versions` 表
  - [ ] version_number（单调递增）
  - [ ] change_summary、snapshot_key
  - [ ] is_rollback
- [ ] 创建 `version_snapshots` 表（元数据，内容在 R2）

### 8.2 存储层

- [ ] 扩展 `storage/r2_client.py`
  - [ ] 支持 snapshots/{study_id}/{version}.json 上传

### 8.3 领域层

- [ ] 实现 `domain/models/version.py`
- [ ] 实现 `domain/services/version_service.py`
  - [ ] create_snapshot（创建快照）
  - [ ] compare_versions（版本对比）
  - [ ] rollback（回滚到指定版本）
  - [ ] get_version_history
- [ ] 扩展 `domain/services/study_service.py`
  - [ ] 关键操作时自动创建快照
  - [ ] 小编辑累积后定期快照（如 10 次操作或 5 分钟）

### 8.4 API 层

- [ ] 实现 `api/schemas/version.py`
- [ ] 实现 `api/endpoints/versions.py`
  - [ ] GET /studies/{id}/versions（版本历史）
  - [ ] GET /studies/{id}/versions/{v}/diff（版本对比）
  - [ ] POST /studies/{id}/rollback

### 8.5 后台任务

- [ ] 实现 `jobs/snapshot_job.py`
  - [ ] 定期版本快照任务

### 8.6 测试

- [ ] 单元测试：`test_version_service.py`
  - [ ] 测试快照创建
  - [ ] 测试版本对比
  - [ ] 测试回滚
- [ ] 集成测试：`test_versions.py`
  - [ ] 测试自动快照策略
  - [ ] 测试版本历史查询
  - [ ] 测试回滚一致性
  - [ ] 测试 R2 快照存储

### 完成标准

- ✅ 所有 checklist 已完成
- ✅ 所有测试通过（覆盖率 > 80%）
- ✅ 关键操作自动创建快照
- ✅ 小编辑累积后定期快照
- ✅ 可以查看版本历史
- ✅ 可以对比两个版本（显示 diff）
- ✅ 可以回滚到指定版本
- ✅ 快照内容正确存储到 R2
- ✅ 产生正确的事件（study.snapshot.created / study.rollback）
- ✅ 代码已提交 git 并 push

---

## Phase 9: 导出与打包

**目标**: 实现异步导出任务（PGN/ZIP）

**参考**: [claude_plan.md § B6. 导出功能](./claude_plan.md#b6-导出功能)

### 9.1 数据库层

- [ ] 创建 `export_jobs` 表（状态机）
  - [ ] status（pending/running/completed/failed）
  - [ ] result_key（R2 中的产物 key）
  - [ ] error_message

### 9.2 领域层

- [ ] 实现 `domain/models/export_job.py`（状态机）
- [ ] 实现 `domain/services/export_service.py`
  - [ ] create_export_job
  - [ ] execute_export（调用 job）
  - [ ] get_export_status

### 9.3 存储层

- [ ] 扩展 `storage/r2_client.py`
  - [ ] 支持 exports/{job_id}.{pgn|zip} 上传
- [ ] 实现 `storage/presign.py`
  - [ ] 生成预签名下载 URL

### 9.4 异步任务

- [ ] 实现 `jobs/runner.py`（任务执行器）
  - [ ] 最简先同步执行
  - [ ] 接口保持异步形态（返回 job_id）
- [ ] 实现 `jobs/export_job.py`
  - [ ] 导出单章节 PGN
  - [ ] 导出整个 study（合并 PGN 或 zip）
  - [ ] 导出 folder/workspace（递归 zip）

### 9.5 API 层

- [ ] 实现 `api/schemas/export.py`
- [ ] 实现 `api/endpoints/exports.py`
  - [ ] POST /export（创建导出任务）
    - Body: { target_id, target_type, format: "pgn" | "zip" }
  - [ ] GET /export/{job_id}（查询状态）
  - [ ] GET /export/{job_id}/download（获取下载链接）

### 9.6 测试

- [ ] 单元测试：`test_export_service.py`
  - [ ] 测试导出 job 创建
  - [ ] 测试状态机转换
- [ ] 集成测试：`test_export_jobs.py`
  - [ ] 测试导出单章节 PGN
  - [ ] 测试导出整个 study
  - [ ] 测试导出 folder（递归）
  - [ ] 测试导出完成事件
  - [ ] 测试预签名下载 URL

### 完成标准

- ✅ 所有 checklist 已完成
- ✅ 所有测试通过（覆盖率 > 80%）
- ✅ 可以导出单章节 PGN
- ✅ 可以导出整个 study（PGN/ZIP）
- ✅ 可以导出 folder/workspace（递归 ZIP）
- ✅ 导出产物正确存储到 R2
- ✅ 可以查询导出任务状态
- ✅ 可以获取预签名下载 URL
- ✅ 产生正确的事件（pgn.export.* ）
- ✅ 代码已提交 git 并 push

---

## Phase 10: 搜索（查找）

**目标**: 实现元数据搜索 + 内容索引

**参考**: [claude_plan.md § D. 搜索 & 索引](./claude_plan.md#d-搜索--索引)

### 10.1 数据库层

- [ ] 创建 `search_index` 表（tsvector）
  - [ ] target_id + target_type
  - [ ] content（索引内容）
  - [ ] search_vector（tsvector 列）
- [ ] 创建 tsvector 触发器（自动更新）

### 10.2 领域层

- [ ] 实现 `domain/services/search_service.py`
  - [ ] search_metadata（DB 查询）
  - [ ] search_content（tsvector 查询）
  - [ ] build_search_query

### 10.3 事件订阅器

- [ ] 扩展 `events/subscribers/search_indexer.py`
  - [ ] 监听所有需要索引的事件
  - [ ] 更新搜索索引
    - [ ] study.* → 索引 study title
    - [ ] study.chapter.* → 索引 chapter title
    - [ ] study.move_annotation.* → 索引 annotation
    - [ ] discussion.* → 索引 discussion 内容

### 10.4 API 层

- [ ] 实现 `api/schemas/search.py`
- [ ] 实现 `api/endpoints/search.py`
  - [ ] GET /search?q={query}
    - Query params: type, scope, sort, page

### 10.5 测试

- [ ] 单元测试：`test_search_service.py`
  - [ ] 测试元数据搜索
  - [ ] 测试内容搜索
- [ ] 集成测试：`test_search_metadata_and_content.py`
  - [ ] 测试写入索引
  - [ ] 测试查询命中
  - [ ] 测试搜索排序
  - [ ] 测试搜索分页

### 完成标准

- ✅ 所有 checklist 已完成
- ✅ 所有测试通过（覆盖率 > 80%）
- ✅ 可以搜索 workspace/folder/study（元数据）
- ✅ 可以搜索 chapter title
- ✅ 可以搜索 move_annotation
- ✅ 可以搜索 discussion 内容
- ✅ 搜索索引自动更新（事件驱动）
- ✅ 搜索结果正确排序和分页
- ✅ 代码已提交 git 并 push

---

## Phase 11: 邮件通知（可选）

**目标**: 实现邮件通知渠道（如果需要）

**参考**: [claude_plan.md § F2. 通知渠道](./claude_plan.md#f2-通知渠道)

### 11.1 邮件渠道

- [ ] 扩展 `notifications/channels/email.py`
  - [ ] 使用 SMTP 或第三方服务（SendGrid/AWS SES）
  - [ ] 渲染邮件模板
  - [ ] 发送邮件

### 11.2 邮件模板

- [ ] 扩展所有通知模板，添加邮件版本
  - [ ] discussion_mention
  - [ ] share_invite
  - [ ] export_complete
  - [ ] study_update

### 11.3 通知聚合

- [ ] 实现 `notifications/aggregator.py`
  - [ ] 批量摘要（每日/每周）
- [ ] 实现 `jobs/notification_digest_job.py`
  - [ ] 定期生成摘要邮件

### 11.4 测试

- [ ] 集成测试：`test_email_notifications.py`
  - [ ] 测试邮件发送
  - [ ] 测试模板渲染
  - [ ] 测试批量摘要

### 完成标准

- ✅ 所有 checklist 已完成
- ✅ 所有测试通过（覆盖率 > 80%）
- ✅ 邮件通知功能正常
- ✅ 邮件模板正确渲染
- ✅ 批量摘要功能正常
- ✅ 代码已提交 git 并 push

---

## Phase 12: 活动日志与审计

**目标**: 实现活动日志记录与查询

**参考**: [claude_plan.md § G3. 活动流](./claude_plan.md#g3-活动流activity-log)

### 12.1 数据库层

- [ ] 创建 `activity_log` 表
  - [ ] actor_id + target_id + action
  - [ ] details（JSON）
  - [ ] timestamp

### 12.2 事件订阅器

- [ ] 实现 `events/subscribers/activity_logger.py`
  - [ ] 监听所有事件
  - [ ] 自动记录活动日志

### 12.3 领域层

- [ ] 实现 `domain/models/activity.py`
- [ ] 实现 `domain/services/activity_service.py`
  - [ ] get_activity_log（带过滤）
  - [ ] get_user_activity
  - [ ] get_object_activity

### 12.4 API 层

- [ ] 实现 `api/endpoints/activity.py`
  - [ ] GET /activity（活动日志查询）
    - Query params: user_id, target_id, action, start_date, end_date

### 12.5 测试

- [ ] 集成测试：`test_activity_log.py`
  - [ ] 测试活动记录
  - [ ] 测试活动查询
  - [ ] 测试过滤（按用户、对象、操作类型）

### 完成标准

- ✅ 所有 checklist 已完成
- ✅ 所有测试通过（覆盖率 > 80%）
- ✅ 所有写操作自动记录活动日志
- ✅ 可以查询 workspace/study 级别的活动
- ✅ 可以查询用户个人的操作历史
- ✅ 可以按用户、对象、操作类型过滤
- ✅ 代码已提交 git 并 push

---

## 总结：如何判断整个项目完成

### 最终验收标准

#### 功能完整性

- [ ] **所有 12 个 Phase 已完成**
- [ ] 所有 Phase 的 checklist 全部 ✅
- [ ] 所有测试通过（单元/集成/API/事件流/协作）
- [ ] 测试覆盖率 > 80%

#### 核心功能验证

- [ ] 可以创建 workspace/folder/study（支持 folder 无限嵌套）
- [ ] 可以分享节点并查看"Shared with me"
- [ ] 可以导入 PGN（自动切割 64 章节）
- [ ] 可以编辑变体树（promote/demote）
- [ ] 可以添加棋步注释（move_annotation）
- [ ] 可以创建讨论并回复（discussion）
- [ ] 可以 @提及用户并收到通知
- [ ] 可以查看在线用户
- [ ] 可以查看版本历史并回滚
- [ ] 可以导出 PGN/ZIP
- [ ] 可以搜索内容
- [ ] 可以查看活动日志

#### 双层评论模型验证（核心创新）

- [ ] **move_annotation** 与 **discussion** 完全分离
- [ ] move_annotation 随 PGN 导出
- [ ] discussion 不随 PGN 导出
- [ ] move_annotation 需要 `editor` 权限
- [ ] discussion 需要 `commenter` 权限

#### 事件系统验证

- [ ] 所有写操作产生事件
- [ ] 事件通过 WebSocket 实时推送
- [ ] 事件驱动通知创建
- [ ] 事件驱动搜索索引更新
- [ ] 事件驱动活动日志记录

#### 文档与代码质量

- [ ] 所有代码已通过 mypy 类型检查
- [ ] 所有代码已通过 ruff lint
- [ ] 所有代码已格式化（black）
- [ ] 关键模块有完整的文档字符串
- [ ] API 文档已生成（OpenAPI/Swagger）

#### 部署准备

- [ ] 数据库迁移脚本已测试
- [ ] 环境变量配置文档已编写
- [ ] Docker/K8s 配置已准备（如需要）
- [ ] 生产环境配置已准备（R2/DB/Redis）

---

## 实施建议

### 开发流程

1. **严格按 Phase 顺序**：不要跳过或并行多个 Phase
2. **Checklist 驱动**：每天开始前看 checklist，结束后更新
3. **测试先行**：写功能前先写测试（TDD）
4. **频繁提交**：每个 checklist 完成后提交一次
5. **Code Review**：每个 Phase 完成后进行 review

### 时间估算（参考）

| Phase | 复杂度 | 估算时间 | 累计时间 |
|-------|--------|---------|---------|
| Phase 0 | 简单 | 1-2 天 | 2 天 |
| Phase 1 | 中等 | 3-5 天 | 7 天 |
| Phase 2 | 中等 | 3-4 天 | 11 天 |
| Phase 3 | 复杂 | 4-6 天 | 17 天 |
| Phase 4 | 中等 | 2-3 天 | 20 天 |
| Phase 5 | 复杂 | 4-5 天 | 25 天 |
| Phase 6 | 复杂 | 4-5 天 | 30 天 |
| Phase 7 | 中等 | 3-4 天 | 34 天 |
| Phase 8 | 中等 | 3-4 天 | 38 天 |
| Phase 9 | 简单 | 2-3 天 | 41 天 |
| Phase 10 | 中等 | 3-4 天 | 45 天 |
| Phase 11 | 简单 | 2-3 天 | 48 天 |
| Phase 12 | 简单 | 2-3 天 | 51 天 |

**总计**: 约 **50-60 工作日**（2-3 个月）

### 风险与应对

| 风险 | 应对 |
|------|------|
| 测试覆盖率不足 | 每个 Phase 结束时检查覆盖率 |
| 事件遗漏 | 每个写操作后检查事件是否产生 |
| 乐观锁冲突处理不当 | 集成测试验证并发场景 |
| R2 存储失败 | 添加重试机制和错误处理 |
| WebSocket 断线重连 | 实现自动重连和状态同步 |

### 每日检查清单

**每日开始前**:
- [ ] 查看当前 Phase 的 checklist
- [ ] 拉取最新代码
- [ ] 运行所有测试确保基础正常

**每日结束时**:
- [ ] 更新 checklist（标记完成项）
- [ ] 提交代码（如有完成项）
- [ ] 运行测试确保没有破坏现有功能
- [ ] 记录遇到的问题和解决方案

---

**最后提醒**:

1. **双层评论模型是核心创新**，必须严格区分 `move_annotation` 和 `discussion`
2. **事件驱动是核心架构**，所有写操作必须产生事件
3. **Folder 可以无限嵌套**，注意路径查询优化
4. **测试覆盖率 > 80%** 是必须达到的标准
5. **严格按 Phase 顺序**，不要跳过或并行

加油！🚀
