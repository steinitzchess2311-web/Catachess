# catchat API — 前端对接文档

> 基础路径：`/api/catchat`
base url: api.catachess.com
> 认证方式：所有接口需要 `Authorization: Bearer <JWT>` 请求头。

---

## 目录

1. [用户搜索](#1-用户搜索)
2. [私聊会话](#2-私聊会话)
3. [消息](#3-消息)
4. [广播](#4-广播管理员专用)
5. [分页说明](#5-分页说明)
6. [错误码](#6-错误码)

---

## 1. 用户搜索

搜索用户（用于发起私聊前查找对方），**使用已有的 workspace 接口**，catchat 不重复实现：

```
GET /api/v1/workspace/users/search?q=<关键词>
Authorization: Bearer <JWT>
```

**响应示例：**
```json
[
  { "id": "uuid-string", "username": "alice" },
  { "id": "uuid-string", "username": "alex" }
]
```

拿到目标用户的 `id` 后，用它来开启会话（见下方）。

---

## 2. 私聊会话

### 获取我的会话列表

```
GET /api/catchat/conversations
Authorization: Bearer <JWT>
```

按最新消息时间倒序排列。

**响应：**
```json
[
  {
    "id": "conv-uuid",
    "other_user_id": "对方用户 uuid",
    "last_message_at": "2026-02-19T10:00:00",
    "created_at": "2026-02-01T08:00:00"
  }
]
```

> `other_user_id` 是对方的 UUID。若需显示对方昵称，用第 1 节的搜索接口查询。

---

### 开启或获取会话

第一次发消息前需调用此接口获取 `conv_id`。**幂等** —— 同一对用户多次调用返回同一个会话。

```
POST /api/catchat/conversations
Authorization: Bearer <JWT>
Content-Type: application/json

{ "user_id": "对方用户 uuid" }
```

**响应（201 Created 或已存在时也 201）：**
```json
{
  "id": "conv-uuid",
  "other_user_id": "对方用户 uuid",
  "last_message_at": "2026-02-19T10:00:00",
  "created_at": "2026-02-01T08:00:00"
}
```

---

## 3. 消息

### 拉取历史消息

```
GET /api/catchat/conversations/{conv_id}/messages?limit=50
Authorization: Bearer <JWT>
```

**Query 参数：**

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `limit` | int | 50 | 每次最多返回条数（1~100） |
| `before` | ISO datetime | — | 分页游标，返回早于此时间的消息 |

**响应（最新消息在前）：**
```json
[
  {
    "id": "msg-uuid",
    "conversation_id": "conv-uuid",
    "sender_id": "发送者 uuid",
    "sender_name": "alice",
    "content": "你好！",
    "created_at": "2026-02-19T10:05:00"
  }
]
```

> 用 `sender_id` 和当前登录用户的 ID 比较，判断消息是"我发的"还是"对方发的"。

---

### 发送消息

```
POST /api/catchat/conversations/{conv_id}/messages
Authorization: Bearer <JWT>
Content-Type: application/json

{ "content": "你好！" }
```

`content` 长度：1～5000 字符。

**响应（201 Created）：**
```json
{
  "id": "msg-uuid",
  "conversation_id": "conv-uuid",
  "sender_id": "我的 uuid",
  "sender_name": "bob",
  "content": "你好！",
  "created_at": "2026-02-19T10:05:00"
}
```

---

## 4. 广播（管理员专用）

全局公告，所有用户可读，只有 `role=admin` 可发送。

### 获取广播列表

```
GET /api/catchat/broadcasts?limit=50
Authorization: Bearer <JWT>
```

**响应（最新在前）：**
```json
[
  {
    "id": "bcast-uuid",
    "sender_id": "admin-uuid",
    "sender_name": "Admin",
    "content": "系统将于今晚维护...",
    "created_at": "2026-02-19T09:00:00"
  }
]
```

### 发送广播（admin 专用）

```
POST /api/catchat/broadcasts
Authorization: Bearer <JWT>   ← 必须是 admin 账号
Content-Type: application/json

{ "content": "系统将于今晚 22:00 进行维护，请提前保存数据。" }
```

**响应（201 Created）：** 同广播列表中的单个对象格式。
非 admin 调用返回 `403 Forbidden`。

---

## 5. 分页说明

消息接口使用**游标分页**（cursor pagination）：

1. 第一次加载：`GET /conversations/{id}/messages?limit=50`
   → 得到最新 50 条，注意响应数组是**最新在前**。

2. 加载更老的消息（下拉历史）：
   取数组最后一条的 `created_at` 作为游标：
   `GET /conversations/{id}/messages?limit=50&before=2026-02-19T10:00:00`

3. 若返回条数 < `limit`，说明已到最早的消息。

---

## 6. 错误码

| HTTP | 含义 |
|------|------|
| 400 | 参数格式错误（如非法 UUID、缺少字段）|
| 401 | 未登录或 token 过期 |
| 403 | 权限不足（如非 admin 发广播）|
| 404 | 会话不存在 |
| 500 | 服务器配置错误（联系后端）|

---

## 快速接入流程

```
1. 搜索用户        GET /api/v1/workspace/users/search?q=alice
2. 开启会话        POST /api/catchat/conversations  { "user_id": "..." }
3. 拉取历史        GET  /api/catchat/conversations/{conv_id}/messages
4. 发送消息        POST /api/catchat/conversations/{conv_id}/messages  { "content": "..." }
5. 展示广播        GET  /api/catchat/broadcasts
```
