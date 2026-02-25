# Classroom 数据库设计

## 总览

新建独立数据库，通过 `username`（VARCHAR(50)，全站唯一，不可修改）与主系统对齐，无跨库外键。
所有表主键使用 UUID v4。删除操作一律软删除（`deleted_at`），保留历史数据完整性。

---

## 表结构

### 1. `classrooms` — 班级

```sql
CREATE TABLE classrooms (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name          VARCHAR(100)  NOT NULL,
    owner         VARCHAR(50)   NOT NULL,  -- 唯一 owner，即创建者
    invite_code   VARCHAR(20)   UNIQUE,    -- 邀请码，可刷新
    invite_active BOOLEAN       NOT NULL DEFAULT TRUE,  -- 邀请码是否启用
    created_at    TIMESTAMPTZ   NOT NULL DEFAULT now(),
    archived_at   TIMESTAMPTZ   NULL,      -- 非 NULL = 已归档（软删除）
    deleted_at    TIMESTAMPTZ   NULL       -- 非 NULL = 彻底删除（保留记录）
);

CREATE INDEX idx_classrooms_owner ON classrooms(owner);
```

**说明：**
- `owner` 是两层角色体系中的顶层，唯一，不在 `classroom_members` 重复存储。
- 归档（`archived_at`）和删除（`deleted_at`）分开：归档可恢复，删除不可逆但保留行。
- `invite_code` 全局唯一，刷新时直接更新该字段。

---

### 2. `classroom_members` — 成员与角色

```sql
CREATE TABLE classroom_members (
    id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    classroom_id  UUID        NOT NULL REFERENCES classrooms(id),
    username      VARCHAR(50) NOT NULL,
    role          VARCHAR(10) NOT NULL CHECK (role IN ('teacher', 'student')),
    -- owner 不在此表，通过 classrooms.owner 判断
    invited_by    VARCHAR(50) NULL,        -- 谁拉进来的
    joined_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    removed_at    TIMESTAMPTZ NULL,        -- 非 NULL = 已被踢/已退出（软删除）
    UNIQUE(classroom_id, username)         -- 一班一人一条记录（含已删除）
);

CREATE INDEX idx_members_classroom ON classroom_members(classroom_id) WHERE removed_at IS NULL;
CREATE INDEX idx_members_username  ON classroom_members(username)     WHERE removed_at IS NULL;
```

**说明：**
- `role` 只有两种：`teacher`（可管理班级）、`student`。owner 身份由 `classrooms.owner` 表达，不在此表。
- `UNIQUE(classroom_id, username)` 包含已删除行——重新邀请同一人时需先检查并恢复（或更新 `removed_at = NULL`），避免插入重复行。
- 活跃成员查询走过滤索引（`WHERE removed_at IS NULL`），性能好。

---

### 3. `assignments` — 任务（材料 / 作业 / 考试三合一）

```sql
CREATE TABLE assignments (
    id            UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    classroom_id  UUID         NOT NULL REFERENCES classrooms(id),
    created_by    VARCHAR(50)  NOT NULL,
    category      VARCHAR(10)  NOT NULL CHECK (category IN ('material', 'assignment', 'exam')),
    type          VARCHAR(20)  NOT NULL,
    -- material:    'workspace' | 'upload'
    -- assignment:  'tactics' | 'opening' | 'trainer' | 'upload'
    -- exam:        'tactics' | 'opening'
    title         VARCHAR(200) NOT NULL,
    description   TEXT         NULL,
    source_type   VARCHAR(20)  NULL CHECK (source_type IN ('study', 'lichess', 'upload', NULL)),
    source_ref    VARCHAR(500) NULL,
    -- study   → '{study_id}/{chapter_id}'
    -- lichess → lichess puzzle set id
    -- upload  → R2 key
    due_date      TIMESTAMPTZ  NULL,       -- NULL = 不限期
    time_limit    INT          NULL,       -- 秒，NULL = 不限时
    max_attempts  SMALLINT     NULL,       -- NULL = 不限次
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT now(),
    deleted_at    TIMESTAMPTZ  NULL
);

CREATE INDEX idx_assignments_classroom ON assignments(classroom_id) WHERE deleted_at IS NULL;
```

---

### 4. `assignment_targets` — 任务对象（全班 or 指定学生）

```sql
CREATE TABLE assignment_targets (
    id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    assignment_id UUID        NOT NULL REFERENCES assignments(id),
    target_type   VARCHAR(10) NOT NULL CHECK (target_type IN ('all', 'user')),
    username      VARCHAR(50) NULL,
    -- target_type='all'  → username=NULL，整个班级
    -- target_type='user' → username 为具体学生
    UNIQUE(assignment_id, username)  -- 防止同一学生重复指定
);

CREATE INDEX idx_targets_assignment ON assignment_targets(assignment_id);
```

**说明：**
- 发布给全班时，插入一条 `target_type='all', username=NULL`。
- 指定学生时，每人插一条 `target_type='user', username=xxx`。
- 查询"这个作业是否对某学生可见"：`target_type='all'` 存在，或 `target_type='user' AND username=?` 存在。

---

### 5. `submissions` — 学生提交记录

```sql
CREATE TABLE submissions (
    id            UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    assignment_id UUID         NOT NULL REFERENCES assignments(id),
    username      VARCHAR(50)  NOT NULL,
    attempt       SMALLINT     NOT NULL DEFAULT 1,
    status        VARCHAR(15)  NOT NULL CHECK (status IN ('in_progress', 'submitted', 'graded')),
    score         REAL         NULL,       -- 0.0~1.0，material 类型为 NULL
    detail        JSONB        NULL,       -- 每题对错等详细数据，按 type 结构不同
    started_at    TIMESTAMPTZ  NOT NULL DEFAULT now(),
    submitted_at  TIMESTAMPTZ  NULL,
    UNIQUE(assignment_id, username, attempt)
);

CREATE INDEX idx_submissions_assignment ON submissions(assignment_id);
CREATE INDEX idx_submissions_username   ON submissions(username);
```

**说明：**
- `score` 统一用 0.0–1.0，前端转成百分比或分数显示。
- `detail` 用 JSONB 存每题详情，结构按 `type` 而定，灵活扩展无需加列。

---

### 6. `assignment_comments` — 老师对提交的批注（可选，V1 可暂不实现）

```sql
CREATE TABLE assignment_comments (
    id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    submission_id UUID        NOT NULL REFERENCES submissions(id),
    author        VARCHAR(50) NOT NULL,
    content       TEXT        NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at    TIMESTAMPTZ NULL
);
```

---

## 软删除策略汇总

| 表 | 字段 | 语义 |
|----|------|------|
| `classrooms` | `archived_at` | 归档（可恢复，学生仍可查历史） |
| `classrooms` | `deleted_at` | 彻底删除（owner 操作，不可恢复） |
| `classroom_members` | `removed_at` | 踢人/退出（重新邀请时可恢复） |
| `assignments` | `deleted_at` | 撤回任务（已有提交记录保留） |
| `assignment_comments` | `deleted_at` | 批注删除 |

所有查询默认加 `WHERE xxx_at IS NULL` 过滤已删除行。

---

## 关键查询示例

**学生的待办作业（临期/逾期）：**
```sql
SELECT a.*
FROM assignments a
JOIN assignment_targets t ON t.assignment_id = a.id
LEFT JOIN submissions s ON s.assignment_id = a.id AND s.username = :username
  AND s.status = 'submitted'
WHERE a.classroom_id IN (
    SELECT classroom_id FROM classroom_members
    WHERE username = :username AND removed_at IS NULL
)
AND a.deleted_at IS NULL
AND (t.target_type = 'all' OR (t.target_type = 'user' AND t.username = :username))
AND s.id IS NULL  -- 还没提交
ORDER BY a.due_date ASC NULLS LAST;
```

**老师端：某作业各学生完成情况：**
```sql
SELECT
    cm.username,
    s.status,
    s.score,
    s.submitted_at,
    s.attempt
FROM classroom_members cm
LEFT JOIN submissions s ON s.assignment_id = :assignment_id AND s.username = cm.username
WHERE cm.classroom_id = :classroom_id
  AND cm.role = 'student'
  AND cm.removed_at IS NULL
ORDER BY cm.username;
```

---

## 与主系统的对齐点

| 对齐项 | 方式 |
|--------|------|
| 用户身份 | `username` VARCHAR(50)，不可改，全站唯一 |
| workspace 联动 | 应用层调 workspace API，用 `source_ref` 存 study/chapter id |
| catchat 联动 | classroom 创建时应用层调 catchat API 创建对应 group，存 `catchat_group_id`（可后续加列） |
| 无跨库外键 | 用户合法性在 API 层校验（查 auth 服务），不依赖 DB 约束 |
