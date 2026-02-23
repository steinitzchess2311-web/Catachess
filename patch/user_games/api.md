# Catachess API 文档

**Base URL**: `https://gameserver.catachess.com`

---

## 目录

1. [健康检查](#1-健康检查)
2. [创建对局](#2-创建对局)
3. [获取当前对局](#3-获取当前对局)
4. [对局详情](#4-对局详情)
5. [历史对局列表](#5-历史对局列表)
6. [中止对局](#6-中止对局)
7. [导出 PGN](#7-导出-pgn)
8. [WebSocket 对局](#8-websocket-对局)

---

## 1. 健康检查

```
GET /health
```

**响应**
```json
{
  "status": "ok",
  "timestamp": "2026-02-23T15:40:22.131254",
  "version": "1.0.0"
}
```

**前端示例**
```js
const res = await fetch('https://gameserver.catachess.com/health')
const data = await res.json()
console.log(data.status) // "ok"
```

---

## 2. 创建对局

```
POST /api/game/create
```

**请求体**
```json
{
  "player_id": "alice",
  "opponent_id": "bob",
  "time_control": {
    "initial": 300,
    "increment": 3
  },
  "color_preference": "random"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `player_id` | string | 创建者 ID |
| `opponent_id` | string | 对手 ID，不能与 player_id 相同 |
| `time_control.initial` | int | 初始时间（秒），1~7200 |
| `time_control.increment` | int | 每步加秒（秒），0~60 |
| `color_preference` | string | `"white"` / `"black"` / `"random"` |

**成功响应** `201`
```json
{
  "game_id": "89375399-246f-4dd6-8caa-fae2bb99f9ab",
  "white_player_id": "alice",
  "black_player_id": "bob",
  "time_control": { "initial": 300, "increment": 3 },
  "status": "waiting",
  "ws_url": "ws://localhost:6767/ws/game/89375399-246f-4dd6-8caa-fae2bb99f9ab",
  "created_at": "2026-02-23T15:40:26.173732Z"
}
```

> ⚠️ `ws_url` 字段目前返回内网地址，前端请忽略，自行拼接：
> `wss://gameserver.catachess.com/ws/game/{game_id}`

**错误响应** `400` - 用户已在对局中
```json
{
  "error": "user_already_in_game",
  "message": "Player alice is already in an active game",
  "current_game_id": "..."
}
```

**前端示例**
```js
async function createGame(playerId, opponentId) {
  const res = await fetch('https://gameserver.catachess.com/api/game/create', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      player_id: playerId,
      opponent_id: opponentId,
      time_control: { initial: 300, increment: 3 },
      color_preference: 'random'
    })
  })

  if (!res.ok) {
    const err = await res.json()
    throw new Error(err.detail?.message || 'Failed to create game')
  }

  const data = await res.json()
  return data.game_id  // 用这个 ID 连接 WebSocket
}
```

---

## 3. 获取当前对局

```
GET /api/game/current?user_id={user_id}
```

用于断线重连或登录后检查是否有未完成对局。

**成功响应** `200` - 有对局
```json
{
  "game_id": "89375399-246f-4dd6-8caa-fae2bb99f9ab",
  "white_player_id": "alice",
  "black_player_id": "bob",
  "your_color": "white",
  "opponent": { "id": "bob" },
  "status": "ongoing",
  "time_control": { "initial": 300, "increment": 3 },
  "current_state": {
    "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "turn": "white",
    "move_count": 0,
    "is_check": false
  },
  "ws_url": "ws://localhost:6767/ws/game/89375399-...",
  "created_at": "2026-02-23T15:40:26.173732Z"
}
```

**成功响应** `200` - 无对局
```json
null
```

**前端示例**
```js
async function checkCurrentGame(userId) {
  const res = await fetch(
    `https://gameserver.catachess.com/api/game/current?user_id=${userId}`
  )
  const data = await res.json()

  if (data) {
    // 有进行中对局，重连 WebSocket
    connectWebSocket(data.game_id, userId)
  }
}
```

---

## 4. 对局详情

```
GET /api/game/{game_id}
```

**成功响应** `200`
```json
{
  "game_id": "89375399-246f-4dd6-8caa-fae2bb99f9ab",
  "white_player_id": "alice",
  "black_player_id": "bob",
  "status": "completed",
  "result": "1-0",
  "end_reason": null,
  "time_control": { "initial": 300, "increment": 3 },
  "moves": [],
  "final_fen": "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2",
  "created_at": "2026-02-23T15:40:26.173732Z",
  "ended_at": "2026-02-23T15:55:00.000000Z"
}
```

**错误响应** `404`
```json
{
  "error": "game_not_found",
  "message": "Game with ID ... not found"
}
```

---

## 5. 历史对局列表

```
GET /api/game/list?user_id={user_id}&limit=20&cursor={cursor}
```

使用游标分页，按创建时间倒序。

| 参数 | 必填 | 说明 |
|------|------|------|
| `user_id` | ✅ | 用户 ID |
| `limit` | ❌ | 每页数量，默认 20，最大 100 |
| `cursor` | ❌ | 上一页返回的 `next_cursor`，首次不传 |

**成功响应** `200`
```json
{
  "games": [
    {
      "game_id": "89375399-...",
      "opponent_id": "bob",
      "your_color": "white",
      "result": "1-0",
      "end_reason": null,
      "status": "completed",
      "move_count": 42,
      "time_control": { "initial": 300, "increment": 3 },
      "created_at": "2026-02-23T15:40:26.173732Z",
      "ended_at": "2026-02-23T15:55:00.000000Z"
    }
  ],
  "next_cursor": "2026-02-23T15:40:26.173732Z",
  "has_more": false
}
```

**前端示例（无限滚动）**
```js
let cursor = null

async function loadMoreGames(userId) {
  const url = new URL('https://gameserver.catachess.com/api/game/list')
  url.searchParams.set('user_id', userId)
  url.searchParams.set('limit', '20')
  if (cursor) url.searchParams.set('cursor', cursor)

  const res = await fetch(url)
  const data = await res.json()

  cursor = data.next_cursor  // 保存给下次请求
  return { games: data.games, hasMore: data.has_more }
}
```

---

## 6. 中止对局

```
POST /api/game/{game_id}/abort
```

**请求体**
```json
{
  "user_id": "alice",
  "reason": "user_request"
}
```

**成功响应** `200`
```json
{
  "success": true,
  "game_id": "89375399-...",
  "status": "aborted"
}
```

**错误响应**

- `403` - 用户不在该对局中
- `400` - 对局已结束，无法中止

---

## 7. 导出 PGN

```
GET /api/game/{game_id}/pgn
```

返回标准 PGN 格式文本（`text/plain`），可导入 Lichess、Chess.com 等软件分析。

**响应示例**
```
[Event "Casual Game"]
[Site "Catachess"]
[Date "2026.02.23"]
[White "alice"]
[Black "bob"]
[Result "1-0"]
[TimeControl "300+3"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 1-0
```

**前端示例**
```js
async function downloadPGN(gameId) {
  const res = await fetch(`https://gameserver.catachess.com/api/game/${gameId}/pgn`)
  const pgn = await res.text()

  // 下载文件
  const blob = new Blob([pgn], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `game-${gameId}.pgn`
  a.click()
}
```

---

## 8. WebSocket 对局

```
wss://gameserver.catachess.com/ws/game/{game_id}?user_id={user_id}
```

### 连接流程

```
1. 调用 POST /api/game/create 获取 game_id
2. 双方各自连接 WebSocket
3. 连接成功后各自收到 game_state 初始状态
4. 双方都连接后服务器自动启动时钟
5. 白方开始走棋
```

### 服务器推送的消息类型

#### `game_state` - 初始状态（连接后立即收到）
```json
{
  "type": "game_state",
  "game_id": "89375399-...",
  "white_player_id": "alice",
  "black_player_id": "bob",
  "your_color": "white",
  "status": "waiting",
  "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
  "turn": "white",
  "move_count": 0,
  "time_remaining": { "white": 300.0, "black": 300.0 }
}
```

#### `move_made` - 走棋完成（广播给双方）
```json
{
  "type": "move_made",
  "move": {
    "san": "e4",
    "uci": "e2e4",
    "from": "e2",
    "to": "e4",
    "captured": null,
    "promotion": null,
    "is_check": false,
    "is_checkmate": false
  },
  "fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1",
  "turn": "black",
  "time_remaining": { "white": 303.0, "black": 300.0 },
  "is_check": false,
  "is_checkmate": false
}
```

#### `time_update` - 时间更新（每秒推送）
```json
{
  "type": "time_update",
  "time_remaining": { "white": 295.5, "black": 300.0 }
}
```

#### `game_over` - 对局结束
```json
{
  "type": "game_over",
  "result": "1-0",
  "reason": "checkmate",
  "winner": "white"
}
```

`reason` 可能的值：`checkmate` / `resignation` / `timeout` / `stalemate` / `draw_agreement` / `insufficient_material` / `fifty_moves` / `threefold_repetition`

#### `draw_offered` - 对手提和
```json
{
  "type": "draw_offered",
  "from_player": "bob"
}
```

#### `opponent_disconnected` / `opponent_reconnected`
```json
{ "type": "opponent_disconnected" }
{ "type": "opponent_reconnected" }
```

#### `error` - 操作失败
```json
{
  "type": "error",
  "error": "invalid_move",
  "message": "Illegal move: e2 to e5"
}
```

#### `pong` - 心跳响应
```json
{ "type": "pong" }
```

---

### 客户端发送的消息类型

#### 走棋
```json
{ "type": "move", "from": "e2", "to": "e4" }
```

兵升变：
```json
{ "type": "move", "from": "e7", "to": "e8", "promotion": "q" }
```
`promotion` 可选值：`"q"` (后) / `"r"` (车) / `"b"` (象) / `"n"` (马)

#### 认输
```json
{ "type": "resign" }
```

#### 提和 / 接受 / 拒绝
```json
{ "type": "offer_draw" }
{ "type": "accept_draw" }
{ "type": "decline_draw" }
```

#### 心跳
```json
{ "type": "ping" }
```

---

### 完整前端示例

```js
async function startGame(myUserId, opponentId) {
  // 1. 创建对局
  const res = await fetch('https://gameserver.catachess.com/api/game/create', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      player_id: myUserId,
      opponent_id: opponentId,
      time_control: { initial: 300, increment: 3 },
      color_preference: 'random'
    })
  })
  const { game_id } = await res.json()

  // 2. 连接 WebSocket
  connectWebSocket(game_id, myUserId)
}

function connectWebSocket(gameId, userId) {
  const ws = new WebSocket(
    `wss://gameserver.catachess.com/ws/game/${gameId}?user_id=${userId}`
  )

  let myColor = null

  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data)

    switch (msg.type) {
      case 'game_state':
        myColor = msg.your_color
        renderBoard(msg.fen)
        updateClock(msg.time_remaining)
        break

      case 'move_made':
        renderBoard(msg.fen)
        updateClock(msg.time_remaining)
        break

      case 'time_update':
        updateClock(msg.time_remaining)
        break

      case 'game_over':
        showResult(msg.result, msg.reason, msg.winner)
        ws.close()
        break

      case 'draw_offered':
        showDrawOffer()
        break

      case 'error':
        console.error(msg.error, msg.message)
        break
    }
  }

  // 走棋
  function makeMove(from, to, promotion = null) {
    ws.send(JSON.stringify({ type: 'move', from, to, promotion }))
  }

  // 心跳（每 25 秒发一次）
  setInterval(() => ws.send(JSON.stringify({ type: 'ping' })), 25000)

  return { ws, makeMove }
}
```

---

*最后更新：2026-02-23*
