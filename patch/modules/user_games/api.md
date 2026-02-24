# API 端点文档

Catachess 游戏服务器 REST API 完整文档

---

## 基础信息

- **Base URL**: `gameserver.catachess.com` - 注意，这是唯一 url，之后的 localhost6767，都请用这个替换。
- **API 前缀**: `/api`
- **内容类型**: `application/json`
- **字符编码**: `UTF-8`

---

## 1. 健康检查

### 1.1 服务器健康检查

检查服务器是否正常运行

**端点**: `GET /health`

**响应**:
```json
{
  "status": "ok",
  "timestamp": "2026-02-07T10:00:00Z",
  "version": "1.0.0"
}
```

**状态码**:
- `200 OK`: 服务器正常

---

## 2. 对局创建 ⭐

### 2.1 创建新对局（指定对手）

双方 ID 均已知时使用（如好友对战，需要知道对手 ID）

**端点**: `POST /api/game/create`

**请求体**:
```json
{
  "player_id": "user123",
  "opponent_id": "user456",
  "time_control": {
    "initial": 300,
    "increment": 3
  },
  "color_preference": "random"
}
```

**字段说明**:
- `player_id`: 创建对局的玩家ID（必需）
- `opponent_id`: 对手玩家ID（必需，不能与 player_id 相同）
- `time_control.initial`: 每方初始时间，1–7200 秒（必需）
- `time_control.increment`: 每步加秒，0–60 秒（必需）
- `color_preference`: `"white"` / `"black"` / `"random"`（默认 `"random"`）

**成功响应** `201 Created`:
```json
{
  "game_id": "550e8400-e29b-41d4-a716-446655440000",
  "white_player_id": "user123",
  "black_player_id": "user456",
  "time_control": {
    "initial": 300,
    "increment": 3
  },
  "status": "waiting",
  "ws_url": "ws://localhost:6767/ws/game/550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2026-02-07T10:00:00Z"
}
```

**错误响应**:

`400 Bad Request` — 玩家已在对局中:
```json
{
  "detail": {
    "error": "user_already_in_game",
    "message": "Player user123 is already in an active game",
    "current_game_id": "550e8400-..."
  }
}
```

---

### 2.2 创建开放对局 ⭐ NEW

生成一个可分享链接的开放对局。**无需预先指定对手**，任何人（登录用户或匿名用户）均可通过链接加入。

**端点**: `POST /api/game/create-open`

**请求体**:
```json
{
  "player_id": "alice",
  "time_control": {
    "initial": 300,
    "increment": 3
  }
}
```

**字段说明**:
- `player_id`: 创建者 ID（必需，min 1 / max 255 字符）
- `time_control.initial`: 初始时间，1–7200 秒（必需，0 会返回 422）
- `time_control.increment`: 每步加秒，0–60 秒（必需）

**成功响应** `201 Created`:
```json
{
  "game_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "open",
  "created_by": "alice"
}
```

**字段说明**:
- `game_id`: 用于构造分享链接和加入请求
- `status`: 固定为 `"open"`，表示等待对手加入
- `created_by`: 创建者 ID

**错误响应**:

`400 Bad Request` — 创建者已在活跃对局中:
```json
{
  "detail": {
    "error": "user_already_in_game",
    "message": "Player alice is already in an active game",
    "current_game_id": "660e8400-..."
  }
}
```

`422 Unprocessable Entity` — 参数校验失败（缺少字段、时间为 0 等）

> **注意**：开放对局创建后有 **10 分钟** 有效期，超时后自动变为 `aborted` 状态。

---

### 2.3 加入开放对局 ⭐ NEW

通过 `game_id` 加入一个处于 `open` 状态的对局。支持登录用户和匿名用户。

**端点**: `POST /api/game/{game_id}/join`

**路径参数**:
- `game_id`: 对局 ID（UUID，来自 create-open 的响应）

**请求体**:
```json
{
  "user_id": "bob"
}
```

或匿名加入（不传 `user_id`）:
```json
{}
```

**字段说明**:
- `user_id`: 加入方用户 ID（可选，不填则服务端生成 `anon_<uuid>` 作为匿名 ID）

**成功响应** `200 OK`:
```json
{
  "game_id": "550e8400-e29b-41d4-a716-446655440000",
  "white_player_id": "bob",
  "black_player_id": "alice",
  "anon_user_id": null
}
```

匿名加入时:
```json
{
  "game_id": "550e8400-e29b-41d4-a716-446655440000",
  "white_player_id": "anon_f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "black_player_id": "alice",
  "anon_user_id": "anon_f47ac10b-58cc-4372-a567-0e02b2c3d479"
}
```

**字段说明**:
- `white_player_id` / `black_player_id`: 服务端随机分配颜色（50/50），加入后才知道谁执白谁执黑
- `anon_user_id`: **仅匿名加入时有值**，前端必须本地保存此 ID，用于后续 WebSocket 连接的 `?user_id=` 参数

**错误响应**:

`404 Not Found` — 对局不存在:
```json
{
  "detail": {
    "error": "game_not_found",
    "message": "Game 550e8400-... not found"
  }
}
```

`400 Bad Request` — 对局已不是 open 状态（已有人加入或已结束）:
```json
{
  "detail": {
    "error": "game_already_started",
    "message": "Game has already started or is not open"
  }
}
```

`400 Bad Request` — 超过 10 分钟有效期:
```json
{
  "detail": {
    "error": "game_expired",
    "message": "Game link has expired (10 minutes)"
  }
}
```

`400 Bad Request` — 创建者尝试加入自己的对局:
```json
{
  "detail": {
    "error": "cannot_join_own_game",
    "message": "Cannot join a game you created"
  }
}
```

---

## 3. 获取当前对局

### 3.1 查询用户当前对局

查询指定用户是否有正在进行的对局（`waiting` 或 `ongoing` 状态）

**端点**: `GET /api/game/current`

**查询参数**:
- `user_id` (必需): 用户ID

**示例**: `GET /api/game/current?user_id=user123`

**成功响应** `200 OK` — 有对局:
```json
{
  "game_id": "550e8400-...",
  "white_player_id": "user123",
  "black_player_id": "user456",
  "your_color": "white",
  "opponent": {
    "id": "user456"
  },
  "status": "ongoing",
  "time_control": {
    "initial": 300,
    "increment": 3
  },
  "current_state": {
    "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "turn": "white",
    "move_count": 0,
    "is_check": false
  },
  "ws_url": "ws://localhost:6767/ws/game/550e8400-...",
  "created_at": "2026-02-07T10:00:00Z"
}
```

**成功响应** `200 OK` — 无对局:
```json
null
```

**用途**: 断线重连时检查是否有进行中的对局。

---

## 4. 对局详情

### 4.1 获取对局完整信息

获取指定对局的完整详情，包括所有移动记录。

**端点**: `GET /api/game/{game_id}`

**路径参数**:
- `game_id`: 对局ID（UUID）

**成功响应** `200 OK`:
```json
{
  "game_id": "550e8400-...",
  "white_player_id": "user123",
  "black_player_id": "user456",
  "status": "completed",
  "result": "1-0",
  "end_reason": "checkmate",
  "time_control": {
    "initial": 300,
    "increment": 3
  },
  "moves": [
    {
      "move_number": 1,
      "white_move": {
        "san": "e4",
        "from": "e2",
        "to": "e4",
        "timestamp": "2026-02-07T10:01:00Z"
      },
      "black_move": {
        "san": "e5",
        "from": "e7",
        "to": "e5",
        "timestamp": "2026-02-07T10:01:30Z"
      }
    }
  ],
  "final_fen": "r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR b KQkq - 4 4",
  "created_by": "user123",
  "created_at": "2026-02-07T10:00:00Z",
  "ended_at": "2026-02-07T10:30:00Z"
}
```

> **注意（open 状态）**: `black_player_id` 在对局尚处于 `open` 状态时为 `null`；`created_by` 标识创建者。

**错误响应**:

`404 Not Found`:
```json
{
  "detail": {
    "error": "game_not_found",
    "message": "Game with ID 550e8400-... not found"
  }
}
```

---

## 5. 历史对局列表

### 5.1 查询用户历史对局

使用游标分页查询用户的历史对局列表。

**端点**: `GET /api/game/list`

**查询参数**:
- `user_id` (必需): 用户ID
- `cursor` (可选): 上次返回的 `next_cursor` 值
- `limit` (可选): 每页数量，默认 20，最大 100

**示例**:
- 第一页: `GET /api/game/list?user_id=user123&limit=20`
- 下一页: `GET /api/game/list?user_id=user123&cursor=2026-02-06T15:00:00Z&limit=20`

**成功响应** `200 OK`:
```json
{
  "games": [
    {
      "game_id": "550e8400-...",
      "opponent_id": "user456",
      "your_color": "white",
      "result": "1-0",
      "end_reason": "checkmate",
      "status": "completed",
      "move_count": 42,
      "time_control": { "initial": 300, "increment": 3 },
      "created_at": "2026-02-07T10:00:00Z",
      "ended_at": "2026-02-07T10:30:00Z"
    }
  ],
  "next_cursor": "2026-02-06T15:00:00Z",
  "has_more": true
}
```

---

## 6. 中止对局

### 6.1 中止进行中的对局

**端点**: `POST /api/game/{game_id}/abort`

**请求体**:
```json
{
  "user_id": "user123",
  "reason": "user_request"
}
```

**成功响应** `200 OK`:
```json
{
  "success": true,
  "game_id": "550e8400-...",
  "status": "aborted"
}
```

**错误响应**:

`403 Forbidden` — 非参与者:
```json
{ "detail": { "error": "not_in_game", "message": "User is not a participant in this game" } }
```

`400 Bad Request` — 对局已结束:
```json
{ "detail": { "error": "game_already_ended", "message": "Cannot abort a game that has already ended" } }
```

---

## 7. 导出对局（PGN）

### 7.1 导出 PGN 格式

**端点**: `GET /api/game/{game_id}/pgn`

**成功响应** `200 OK` (`text/plain`):
```
[Event "Casual Game"]
[White "user123"]
[Black "user456"]
[Result "1-0"]
[TimeControl "300+3"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 1-0
```

---

## 8. 开放对局 — 前端完整流程与代码范例 ⭐ NEW

### 对局状态机

```
open  ──(join)──►  waiting  ──(两端WS均连接)──►  ongoing  ──►  completed
  │                                                               aborted
  └──(10分钟超时)──► aborted
```

---

### 8.1 创建者流程（房主端）

```javascript
// ① 创建开放对局
async function createOpenGame(playerId, initialSec, incrementSec) {
  const res = await fetch('/api/game/create-open', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      player_id: playerId,
      time_control: { initial: initialSec, increment: incrementSec }
    })
  });

  if (!res.ok) {
    const err = await res.json();
    if (err.detail?.error === 'user_already_in_game') {
      alert('你已在一个活跃对局中');
    }
    throw new Error(err.detail?.error);
  }

  const { game_id, status, created_by } = await res.json();
  // status === 'open'

  // ② 构造分享链接（前端路由，不是后端路由）
  const shareUrl = `${location.origin}/game/${game_id}/join`;
  console.log('分享此链接给对手：', shareUrl);

  // ③ 等待对手加入后再连接 WebSocket
  // 轮询 GET /api/game/{game_id} 或通过其他通知机制
  await waitForOpponent(game_id);

  // ④ 连接 WebSocket（对局进入 waiting 状态后才有效）
  connectWebSocket(game_id, created_by);
}

// 简单轮询示例（生产环境可换成长轮询或 SSE）
async function waitForOpponent(gameId, intervalMs = 2000) {
  while (true) {
    const res = await fetch(`/api/game/${gameId}`);
    const game = await res.json();
    if (game.status === 'waiting' || game.status === 'ongoing') return game;
    if (game.status === 'aborted') throw new Error('game_expired');
    await new Promise(r => setTimeout(r, intervalMs));
  }
}
```

---

### 8.2 加入者流程（已登录用户）

```javascript
// 从分享链接中取得 game_id（例如路由参数）
async function joinAsUser(gameId, userId) {
  const res = await fetch(`/api/game/${gameId}/join`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId })
  });

  if (!res.ok) {
    const err = await res.json();
    switch (err.detail?.error) {
      case 'game_not_found':     alert('对局不存在'); break;
      case 'game_already_started': alert('对局已有人加入'); break;
      case 'game_expired':       alert('邀请链接已过期（10分钟）'); break;
      case 'cannot_join_own_game': alert('不能加入自己创建的对局'); break;
    }
    throw new Error(err.detail?.error);
  }

  const { game_id, white_player_id, black_player_id, anon_user_id } = await res.json();
  // anon_user_id === null（已登录用户）

  // 颜色由服务端随机分配
  const myColor = white_player_id === userId ? 'white' : 'black';
  console.log('我的颜色：', myColor);

  connectWebSocket(game_id, userId);
}
```

---

### 8.3 加入者流程（匿名用户）

```javascript
async function joinAnonymous(gameId) {
  const res = await fetch(`/api/game/${gameId}/join`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({})   // 不传 user_id
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail?.error);
  }

  const { game_id, white_player_id, black_player_id, anon_user_id } = await res.json();
  // anon_user_id = "anon_f47ac10b-58cc-4372-a567-0e02b2c3d479"

  // ⚠️ 必须本地持久化！刷新页面后无法重新获取
  sessionStorage.setItem(`anon_id_${game_id}`, anon_user_id);

  const myColor = white_player_id === anon_user_id ? 'white' : 'black';
  console.log('匿名用户 ID：', anon_user_id, '颜色：', myColor);

  connectWebSocket(game_id, anon_user_id);
}
```

---

### 8.4 WebSocket 连接（open 状态下不可连接）

```javascript
function connectWebSocket(gameId, userId) {
  const ws = new WebSocket(
    `ws://localhost:6767/ws/game/${gameId}?user_id=${userId}`
  );

  ws.onclose = (event) => {
    switch (event.code) {
      case 4003: console.error('你不在此对局中'); break;
      case 4004: console.error('对局不存在'); break;
      case 4005: console.error('对局已被中止'); break;
      case 4006: console.error('对局已结束'); break;
      case 4007:
        // 对局仍处于 open 状态，还没有对手加入
        // 创建者在等待对手时不应提前连接 WebSocket
        console.warn('对局尚未开始，等待对手加入后再连接');
        break;
    }
  };

  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    // 处理 game_state、move、error 等消息类型
  };
}
```

> **WS Close Code 说明**:
> | Code | 含义 |
> |------|------|
> | 4003 | 用户不在该对局中 |
> | 4004 | 对局不存在 |
> | 4005 | 对局已中止（`aborted`） |
> | 4006 | 对局已完成（`completed`） |
> | 4007 | 对局尚处于 `open` 状态，未有对手加入，禁止 WS 连接 |

---

### 8.5 完整开放对局时序图

```
创建者(Alice)               服务器                    加入者(Bob/匿名)
     │                        │                              │
     │── POST /create-open ──►│                              │
     │◄── {game_id, "open"} ──│                              │
     │                        │                              │
     │   分享 game_id 给 Bob  │                              │
     │ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─│─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─►│
     │                        │                              │
     │                        │◄── POST /{game_id}/join ─────│
     │                        │── {game_id, white, black} ──►│
     │                        │   status: "waiting"          │
     │                        │                              │
     │── WS /ws/game/{id} ───►│◄─── WS /ws/game/{id} ────────│
     │◄── initial_state ──────│──── initial_state ──────────►│
     │   (双方均连接后)        │                              │
     │◄── game started ───────│──── game started ───────────►│
     │                        │                              │
```

---

## 端点速查表

| 方法 | 路径 | 说明 | 状态码 |
|------|------|------|--------|
| `GET` | `/health` | 健康检查 | 200 |
| `POST` | `/api/game/create` | 创建对局（指定对手） | 201 |
| `POST` | `/api/game/create-open` | **创建开放对局** | 201 |
| `POST` | `/api/game/{id}/join` | **加入开放对局** | 200 |
| `GET` | `/api/game/current` | 获取当前对局 | 200 |
| `GET` | `/api/game/list` | 历史对局列表 | 200 |
| `GET` | `/api/game/{id}` | 对局详情 | 200 |
| `POST` | `/api/game/{id}/abort` | 中止对局 | 200 |
| `GET` | `/api/game/{id}/pgn` | 导出 PGN | 200 |
| `WS` | `/ws/game/{id}` | WebSocket 对局连接 | — |

---

## 错误码汇总

| error 字段 | HTTP | 触发场景 |
|---|---|---|
| `user_already_in_game` | 400 | 用户已在 open/waiting/ongoing 对局中 |
| `game_not_found` | 404 | game_id 不存在 |
| `game_already_started` | 400 | 对局已不是 open 状态 |
| `game_expired` | 400 | open 对局超过 10 分钟未有人加入 |
| `cannot_join_own_game` | 400 | 创建者尝试加入自己的对局 |
| `not_in_game` | 403 | 无权限操作该对局 |
| `game_already_ended` | 400 | 对局已结束，无法中止 |
| `invalid_cursor` | 400 | 历史列表游标格式错误 |

---

## 注意事项

1. **匿名用户 ID 持久化**: 匿名加入后返回的 `anon_user_id` 仅返回一次，前端必须自行保存（`sessionStorage` / `localStorage`），用于 WebSocket 连接和断线重连
2. **颜色随机分配**: 加入对局时服务端随机决定谁执白谁执黑，前端在 join 响应后才能知道颜色
3. **open 状态 WS 禁止连接**: 对局处于 `open` 时 WebSocket 连接会被服务端以 close code `4007` 拒绝，应等待 join 完成后再建立连接
4. **10 分钟有效期**: `open` 对局超时后服务端自动改为 `aborted`，加入时会收到 `game_expired` 错误
5. **用户认证**: 当前版本未实现 JWT 认证，生产环境需补充
6. **时间格式**: 所有时间戳为 ISO 8601（UTC）

---

## 版本历史

- **v1.1.0** (2026-02-23): 新增开放对局（`create-open` / `join`），`GameDetail` 增加 `created_by` 字段，`black_player_id` 改为可选
- **v1.0.0** (2026-02-07): 初始版本，实现核心对局 API
catadragon@catadragon:~/Code/catachess/catachess_game/catachess