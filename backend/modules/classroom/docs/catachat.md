# Classroom × Catachat 联动设计

## 核心原则

- **Classroom 是权威**：成员关系、角色、班级状态以 classroom DB 为准。
- **Catachat 是通道**：消息收发、通知推送全走 catachat，classroom 不自建消息系统。
- **最终一致**：两库无分布式事务，classroom 操作优先，catachat 同步失败只记日志，不回滚。

---

## 数据库改动

在 `classrooms` 表加一列：

```sql
ALTER TABLE classrooms
    ADD COLUMN catchat_group_id UUID NULL;
```

- 创建班级成功后写入，失败则为 NULL（可重试同步）。
- classroom 查询不依赖此字段，仅用于转发 catachat 操作。

---

## 生命周期同步

### 创建班级

```
classroom API
  1. INSERT classrooms（name, owner, ...）
  2. INSERT classroom_members（owner, role='teacher'）
  3. → catchat POST /groups
       { name: 班级名, members: [{ user_id, username }, ...] }
  4. 拿到 catchat group_id → UPDATE classrooms SET catchat_group_id=...
```

catchat group 初始角色映射：

| Classroom 角色 | Catachat 角色 |
|---------------|--------------|
| owner | owner |
| teacher | admin |
| student | member |

---

### 拉人进班

```
classroom API
  1. INSERT classroom_members（username, role）
  2. → catchat POST /groups/{catchat_group_id}/members
       { user_id, username, role: 映射后的 catachat role }
```

---

### 踢人 / 退出

```
classroom API
  1. UPDATE classroom_members SET removed_at=now()
  2. → catchat DELETE /groups/{catchat_group_id}/members/{user_id}
```

---

### 角色变更（student ↔ teacher）

```
classroom API
  1. UPDATE classroom_members SET role=...
  2. → catchat PATCH /groups/{catchat_group_id}/members/{user_id}
       { role: 映射后的 catachat role }
```

---

### 班级改名

```
classroom API
  1. UPDATE classrooms SET name=...
  2. → catchat PATCH /groups/{catchat_group_id}
       { name: 新名称 }
```

---

### 归档班级

- classroom：SET archived_at=now()
- catachat：**不解散 group**，保留历史消息，成员仍可查看。
- 可在前端对已归档班级的聊天入口加"只读"标记（UI 层处理）。

---

### 解散班级（彻底删除）

```
classroom API
  1. UPDATE classrooms SET deleted_at=now()
  2. → catchat DELETE /groups/{catchat_group_id}
```

---

## 加人时的字段要求

Catachat `catchat_group_members` 同时需要 `user_id`（UUID）和 `username`。

Classroom 自身只存 `username`，因此"加人"接口需前端同时传两个字段：

```json
POST /classroom/{id}/members
{
  "username": "alice",
  "user_id": "5724ce80-ca7c-4eb2-9e10-e8089d3a28a8"
}
```

`user_id` 仅透传给 catachat，不存入 classroom DB。

**前端获取方式**：搜索用户时 auth 服务返回 `{ username, user_id }`，一并带到加人请求里。

---

## 同步失败处理

| 场景 | 处理方式 |
|------|---------|
| 创建班级时 catachat 建群失败 | `catchat_group_id` 保持 NULL，记错误日志 |
| 加人/踢人同步失败 | classroom 操作已落库，记错误日志，不回滚 |
| 改名/改角色同步失败 | 同上 |
| `catchat_group_id` 为 NULL 时触发写操作 | 跳过 catachat 调用，仅操作 classroom DB |

后续可加管理接口 `POST /classroom/{id}/sync-catachat`，重建 catachat group 并补齐成员，用于修复不一致状态。

---

## 前端使用方式

- 班级详情页的"消息"入口：用 `catchat_group_id` 直接跳转到 catachat 对应 group。
- 学生端公告区：读 catachat group 最近消息，点击进入 catachat。
- Broadcast（广播）：老师在 classroom 发公告 → 调 catachat `POST /broadcasts`，`group_id` 为 `catchat_group_id`。

---

## 不由 Classroom 管理的部分

以下功能完全交给 catachat，classroom 不干预：

- 消息内容、已读状态、消息通知。
- 群内固定消息（pin）、表情回应等 catachat 自有功能。
- catachat 侧的权限校验（classroom 只负责同步角色，不重复鉴权）。
