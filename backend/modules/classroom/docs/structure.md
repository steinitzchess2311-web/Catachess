# Classroom 模块代码结构

挂载路径：`/api/classroom`
独立数据库：`CLASSROOM_DATABASE` 环境变量（Railway PostgreSQL）

```
backend/modules/classroom/
├── docs/                          # 设计文档（不进入生产）
│   ├── structure.md               # 本文件：模块结构说明
│   ├── database.md                # 数据库表设计
│   ├── api.md                     # API 端点设计
│   ├── catachat.md                # Catachat 联动设计
│   ├── functions.md               # 功能范围文档
│   ├── brainstorm.md              # 原始需求头脑风暴
│   └── env.md                     # 环境变量（gitignore）
│
├── __init__.py
├── auth.py                        # [鉴权] JWT 解析，返回 User 对象
│                                  #   复用主系统 JWT + users 表，与 catchat/auth.py 完全一致
│
├── db/
│   ├── __init__.py
│   ├── session.py                 # [数据库] engine、Base、get_db()
│   │                              #   读取 CLASSROOM_DATABASE env var
│   │                              #   同步 SQLAlchemy（与 catchat 一致）
│   └── models/
│       ├── __init__.py            # 统一 import 所有 model，供 create_all 使用
│       ├── classroom.py           # classrooms 表
│       │                          #   id, name, owner, invite_code, invite_active
│       │                          #   catchat_group_id, created_at, archived_at, deleted_at
│       ├── member.py              # classroom_members 表
│       │                          #   id, classroom_id, username, role, invited_by
│       │                          #   joined_at, removed_at
│       │                          #   UNIQUE(classroom_id, username)
│       ├── assignment.py          # assignments 表
│       │                          #   id, classroom_id, created_by, category, type
│       │                          #   title, description, source_type, source_ref
│       │                          #   due_date, time_limit, max_attempts
│       │                          #   created_at, deleted_at
│       ├── target.py              # assignment_targets 表
│       │                          #   id, assignment_id, target_type, username
│       │                          #   target_type='all' → username=NULL（全班）
│       │                          #   target_type='user' → username=具体学生
│       └── submission.py          # submissions 表
│                                  #   id, assignment_id, username, attempt
│                                  #   status, score, detail(JSONB)
│                                  #   started_at, submitted_at
│
├── schemas/
│   ├── __init__.py
│   ├── classroom.py               # [Pydantic] ClassroomCreate/Update/Response
│   │                              #   ClassroomListItem（含 my_role, member_count）
│   ├── member.py                  # [Pydantic] MemberAdd/Response/RoleUpdate
│   ├── assignment.py              # [Pydantic] AssignmentCreate/Update/Response
│   │                              #   TargetSpec（all vs users）
│   │                              #   AssignmentListItem（老师视角 + 学生视角）
│   └── submission.py              # [Pydantic] SubmissionUpsert/Response
│                                  #   AssignmentStats（老师统计面板）
│                                  #   TodoItem（学生代办，含 urgency）
│
├── services/
│   ├── __init__.py
│   ├── catachat_sync.py           # [Catachat 联动] 直接操作 catchat DB（同进程）
│   │                              #   sync_create_group() — 建班时创建 group
│   │                              #   sync_add_member()   — 加人时同步
│   │                              #   sync_remove_member()— 踢人时同步
│   │                              #   sync_update_role()  — 改角色时同步
│   │                              #   sync_rename_group() — 改名时同步
│   │                              #   sync_dissolve_group()— 解散时同步
│   │                              #   所有方法 try/except，失败只记日志，不抛异常
│   └── todo.py                    # [代办服务] 学生跨班代办汇总逻辑
│                                  #   get_my_todo(username, db) → list[TodoItem]
│                                  #   urgency 计算：overdue / due_soon(≤48h) / normal
│
└── api/
    ├── __init__.py
    ├── router.py                  # 聚合所有子路由，挂载到 /api/classroom
    └── endpoints/
        ├── __init__.py
        ├── classrooms.py          # [端点] 班级 CRUD + 归档/恢复 + 邀请码管理
        │                          #   POST   /classrooms
        │                          #   GET    /classrooms
        │                          #   GET    /classrooms/{id}
        │                          #   PATCH  /classrooms/{id}
        │                          #   DELETE /classrooms/{id}
        │                          #   POST   /classrooms/{id}/archive
        │                          #   POST   /classrooms/{id}/unarchive
        │                          #   GET    /classrooms/{id}/invite
        │                          #   POST   /classrooms/{id}/invite/reset
        │                          #   PATCH  /classrooms/{id}/invite
        │                          #   POST   /classrooms/join
        │                          #   GET    /classrooms/{id}/chat
        │                          #   POST   /classrooms/{id}/broadcast
        ├── members.py             # [端点] 成员管理
        │                          #   GET    /classrooms/{id}/members
        │                          #   POST   /classrooms/{id}/members
        │                          #   DELETE /classrooms/{id}/members/{username}
        │                          #   PATCH  /classrooms/{id}/members/{username}/role
        │                          #   POST   /classrooms/{id}/members/leave
        ├── assignments.py         # [端点] 任务发布与管理
        │                          #   POST   /classrooms/{id}/assignments
        │                          #   GET    /classrooms/{id}/assignments
        │                          #   GET    /classrooms/{id}/assignments/{aid}
        │                          #   PATCH  /classrooms/{id}/assignments/{aid}
        │                          #   DELETE /classrooms/{id}/assignments/{aid}
        │                          #   GET    /classrooms/{id}/assignments/{aid}/stats
        └── submissions.py         # [端点] 提交记录 + 学生代办
                                   #   POST   /classrooms/{id}/assignments/{aid}/submissions
                                   #   GET    /classrooms/{id}/assignments/{aid}/submissions
                                   #   GET    /classrooms/{id}/assignments/{aid}/submissions/me
                                   #   GET    /classrooms/{id}/assignments/{aid}/submissions/{username}
                                   #   GET    /classrooms/my/todo
```

---

## 关键设计原则

1. **auth.py 直接复用主系统**：JWT decode + 查 users 表，与 catchat/auth.py 完全相同，classroom 无自己的用户表。
2. **db/session.py 独立**：指向 `CLASSROOM_DATABASE`，与 workspace/catchat 数据库完全隔离。
3. **catachat_sync.py 同进程直接调**：不走 HTTP，直接 import catchat DB models 操作，零延迟，失败静默。
4. **services/ 封装业务逻辑**：端点只做参数校验 + 权限检查，复杂查询逻辑下沉到 services。
5. **schemas/ 严格分层**：Request schema（Create/Update）与 Response schema 分开，不混用。
