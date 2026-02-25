# Classroom API 设计

挂载路径：`/api/classroom`
鉴权：所有端点需 JWT token（与现有系统一致）。
角色简写：**O** = owner，**T** = teacher（含 owner），**S** = student，**Any** = 班级任意成员

---

## 一、班级管理

### 班级 CRUD

```
POST   /classrooms                    创建班级               登录用户
GET    /classrooms                    我的班级列表            登录用户
GET    /classrooms/{id}               班级详情 + 成员列表     Any
PATCH  /classrooms/{id}               改名                   T
DELETE /classrooms/{id}               解散班级（软删除）      O
POST   /classrooms/{id}/archive       归档班级               O
POST   /classrooms/{id}/unarchive     恢复归档               O
```

**POST /classrooms**
```json
Request:  { "name": "初级班A" }
Response: { "id", "name", "owner", "invite_code", "catchat_group_id", "created_at" }
```
后端同步：创建 catachat group，写回 `catchat_group_id`。

**GET /classrooms**
```json
Response: [
  {
    "id", "name", "owner", "my_role",   // my_role: 'owner'|'teacher'|'student'
    "member_count", "archived_at", "created_at"
  }
]
```
返回"我是成员"或"我是 owner"的所有班级，已删除（`deleted_at != NULL`）不返回。

**PATCH /classrooms/{id}**
```json
Request:  { "name": "新班级名" }
Response: { "id", "name", ... }
```
同步更新 catachat group 名称。

**DELETE /classrooms/{id}**
- 软删除：`deleted_at = now()`
- 同步解散 catachat group
- 已有 assignments/submissions 数据保留

---

### 邀请码

```
GET    /classrooms/{id}/invite        获取当前邀请码         T
POST   /classrooms/{id}/invite/reset  刷新邀请码             T
PATCH  /classrooms/{id}/invite        启用/禁用邀请码        T
POST   /classrooms/join               用邀请码加入班级       登录用户
```

**POST /classrooms/join**
```json
Request:  { "invite_code": "ABC123" }
Response: { "classroom_id", "name", "role": "student" }
```
后端同步：加入对应 catachat group（role=member）。

---

### 成员管理

```
GET    /classrooms/{id}/members                   成员列表           Any
POST   /classrooms/{id}/members                   拉人进班           T
DELETE /classrooms/{id}/members/{username}        踢人               T（不可踢 owner）
PATCH  /classrooms/{id}/members/{username}/role   改角色             O
POST   /classrooms/{id}/members/leave             自己退出班级       S/T（owner 不可退）
```

**POST /classrooms/{id}/members**
```json
Request:  { "username": "alice", "user_id": "uuid", "role": "student" }
// user_id 透传给 catachat，不存 classroom DB
Response: { "username", "role", "joined_at" }
```

**PATCH /classrooms/{id}/members/{username}/role**
```json
Request:  { "role": "teacher" | "student" }
```
同步更新 catachat group member role（teacher→admin，student→member）。

---

## 二、任务管理（材料 / 作业 / 考试）

### 任务 CRUD

```
POST   /classrooms/{id}/assignments              发布任务           T
GET    /classrooms/{id}/assignments              班级任务列表       Any
GET    /classrooms/{id}/assignments/{aid}        任务详情           Any
PATCH  /classrooms/{id}/assignments/{aid}        编辑任务           T（创建者）
DELETE /classrooms/{id}/assignments/{aid}        撤回任务（软删除） T（创建者）
```

**POST /classrooms/{id}/assignments**
```json
Request:
{
  "category": "material" | "assignment" | "exam",
  "type": "workspace" | "upload" | "tactics" | "opening" | "trainer",
  "title": "开局作业第一期",
  "description": "...",
  "source_type": "study" | "lichess" | "upload" | null,
  "source_ref": "study_id/chapter_id 或 R2 key 或 lichess id",
  "due_date": "2026-03-01T23:59:00Z" | null,
  "time_limit": 1800 | null,
  "max_attempts": 3 | null,
  "targets": {
    "type": "all"
    // 或
    "type": "users",
    "usernames": ["alice", "bob"]
  }
}

Response: { "id", "title", "category", "type", "due_date", "targets", "created_at" }
```

**GET /classrooms/{id}/assignments**
Query params：`?category=assignment&status=pending`（status 对学生有效：pending/submitted/overdue）
```json
Response: [
  {
    "id", "title", "category", "type", "due_date",
    "my_submission": { "status", "score", "attempt" } | null  // 学生视角
    "submission_count": 12, "member_count": 20               // 老师视角
  }
]
```

---

### 提交

```
POST   /classrooms/{id}/assignments/{aid}/submissions        开始/提交           S
GET    /classrooms/{id}/assignments/{aid}/submissions        所有学生提交列表    T
GET    /classrooms/{id}/assignments/{aid}/submissions/me     我的提交记录        S
GET    /classrooms/{id}/assignments/{aid}/submissions/{uid}  单个学生的提交      T
```

**POST /classrooms/{id}/assignments/{aid}/submissions**
```json
Request:
{
  "status": "in_progress" | "submitted",
  "score": 0.85 | null,
  "detail": { ... }   // 按 type 自定义，存 JSONB
}
// 首次调用 status=in_progress 创建记录，再次调用 status=submitted 完成提交
// attempt 由后端根据该学生已有记录自动递增
```

---

## 三、老师端统计

```
GET /classrooms/{id}/assignments/{aid}/stats    作业统计
```

**Response:**
```json
{
  "assignment_id",
  "total_targets": 20,
  "submitted": 14,
  "in_progress": 2,
  "not_started": 4,
  "overdue": 3,
  "avg_score": 0.73,
  "score_distribution": [0.2, 0.5, 0.73, 0.85, 1.0],  // 每个学生的 score
  "per_student": [
    { "username", "status", "score", "attempt", "submitted_at" }
  ]
}
```

---

## 四、学生端代办

```
GET /classrooms/my/todo    我的所有班级待办汇总
```

**Response:**
```json
[
  {
    "assignment_id", "title", "category", "classroom_name",
    "due_date", "urgency": "overdue" | "due_soon" | "normal",
    "my_status": "not_started" | "in_progress" | "submitted"
  }
]
```
`due_soon` 定义：距 due_date ≤ 48 小时且未提交。

---

## 五、Catachat 联动入口

```
GET /classrooms/{id}/chat    获取 catchat_group_id（前端用来跳转）
```

**Response:**
```json
{ "catchat_group_id": "uuid" | null }
```
为 null 时前端提示"消息功能暂不可用"。

```
POST /classrooms/{id}/broadcast    发班级公告（走 catachat broadcasts）
```
```json
Request:  { "content": "本周五有考试，请提前准备。" }
Response: { "broadcast_id", "created_at" }
```
后端调 `POST /api/catchat/broadcasts`，`group_id` = `catchat_group_id`。

---

## 六、权限矩阵汇总

| 端点 | owner | teacher | student |
|------|:-----:|:-------:|:-------:|
| 创建班级 | ✓ | ✓（自建） | ✓（自建） |
| 改名 / 归档 / 解散 | ✓ | — | — |
| 拉人 / 踢人 | ✓ | ✓ | — |
| 改成员角色 | ✓ | — | — |
| 发布/编辑/撤回任务 | ✓ | ✓ | — |
| 查看任务列表 | ✓ | ✓ | ✓ |
| 提交作业 | — | — | ✓ |
| 查看所有提交 / 统计 | ✓ | ✓ | — |
| 查看自己提交 | — | — | ✓ |
| 发公告 | ✓ | ✓ | — |
| 刷新邀请码 | ✓ | ✓ | — |

---

## 七、错误码约定

| HTTP | 场景 |
|------|------|
| 400 | 参数错误（缺字段、格式错误） |
| 403 | 权限不足 |
| 404 | 班级/任务/成员不存在 |
| 409 | 重复操作（用户已是成员、邀请码冲突） |
| 422 | 业务规则冲突（超出 max_attempts、已过 due_date） |
