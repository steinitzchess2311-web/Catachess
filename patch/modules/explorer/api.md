# Catachess Opening Explorer API

**Base URL**: `https://database.catachess.com`

所有接口均为 `GET` 请求，返回 `application/json`（`/player` 除外，返回 NDJSON 流）。
无需鉴权，支持跨域（CORS 全开放）。

---

## 目录

- [通用说明](#通用说明)
- [GET /masters](#get-masters)
- [GET /masters/games](#get-mastersgames)
- [GET /search/players](#get-searchplayers)
- [GET /search/games](#get-searchgames)
- [GET /lichess](#get-lichess)
- [GET /player](#get-player)
- [GET /game/{id}](#get-gameid)
- [GET /health](#get-health)
- [响应结构参考](#响应结构参考)
- [错误处理](#错误处理)
- [前端接入示例](#前端接入示例)

---

## 通用说明

### FEN 参数

所有接口都接受标准 FEN 字符串描述棋盘局面。FEN 中的空格需 URL 编码为 `+` 或 `%20`。

```
rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1
→ URL: rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR+w+KQkq+-+0+1
```

### play 参数

在 FEN 基础上追加走法，格式为逗号分隔的 UCI 走法序列：

```
e2e4,e7e5,g1f3
```

服务会按顺序应用这些走法后再查询当前局面。这样前端只需传起始 FEN + 走法列表，无需计算中间局面 FEN。

### 走法编码（UCI）

格式：`<起始格><目标格>[升变棋子]`

- 普通走法：`e2e4`、`g1f3`
- 兵升变：`e7e8q`（升后）、`e7e8r`（升车）、`e7e8b`（升象）、`e7e8n`（升马）

### cursor 分页

`/masters/games` 和 `/search/games` 使用 cursor 分页而非页码分页。

- 首页不传 `cursor`
- 响应中的 `next_cursor` 传给下一次请求的 `cursor` 参数
- `next_cursor` 为 `null` 表示已是最后一页
- cursor 为不透明字符串，前端直接透传，无需解析

---

## GET /masters

查询大师赛（TWIC 数据库，460 万局）开局统计。

### 请求参数

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `fen` | string | ✓ | — | 棋盘局面 FEN |
| `play` | string | ✗ | `""` | 在 FEN 基础上追加的 UCI 走法，逗号分隔 |
| `since` | integer | ✗ | null | 过滤：仅统计此年份及之后的对局（如 `2020`） |
| `until` | integer | ✗ | null | 过滤：仅统计此年份及之前的对局（如 `2024`） |
| `moves` | integer | ✗ | `12` | 返回的候选走法数量上限（0–100） |
| `topGames` | integer | ✗ | `15` | 返回的精选对局数量上限（0–15） |

### 响应

```json
{
  "white": 2183001,
  "draws": 1165023,
  "black": 1255817,
  "moves": [
    {
      "uci": "e2e4",
      "san": "e4",
      "white": 884788,
      "draws": 533555,
      "black": 764828,
      "averageRating": 2541,
      "game": {
        "id": "a3f2c1d8",
        "white": { "name": "Carlsen, Magnus", "rating": 2882 },
        "black": { "name": "Nepomniachtchi, Ian", "rating": 2795 },
        "winner": "white",
        "year": 2023
      }
    }
  ],
  "topGames": [
    {
      "id": "a3f2c1d8",
      "white": { "name": "Carlsen, Magnus", "rating": 2882 },
      "black": { "name": "Nepomniachtchi, Ian", "rating": 2795 },
      "winner": "white",
      "year": 2023
    }
  ],
  "recentGames": [],
  "opening": null
}
```

### 示例

```bash
# 查询起始局面
GET /masters?fen=rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR+w+KQkq+-+0+1

# 查询 1.e4 e5 之后的局面
GET /masters?fen=rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR+w+KQkq+-+0+1&play=e2e4,e7e5

# 只看 2020 年之后的对局，返回前 5 种走法
GET /masters?fen=...&since=2020&moves=5
```

---

## GET /masters/games

给定局面，返回经过该局面的**全部对局**（无 15 局限制），支持三种排序方式和无限滚动分页。

### 请求参数

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `fen` | string | ✓ | — | 棋盘局面 FEN |
| `sort` | string | ✗ | `elo_desc` | 排序方式，见下表 |
| `limit` | integer | ✗ | `20` | 每页数量（1–50） |
| `cursor` | string | ✗ | null | 分页游标，来自上次响应的 `next_cursor` |
| `player` | string[] | ✗ | `[]` | 棋手精确名字（来自 `/search/players`），可多次传入实现合并棋手 |
| `player_result` | string | ✗ | null | 从棋手视角过滤结果：`win`（该棋手赢）/ `loss`（该棋手输）/ `draw`（平局）。必须同时传 `player=`。 |

**sort 可选值**：

| 值 | 说明 |
|----|------|
| `elo_desc` | 按平均等级分从高到低（默认） |
| `year_desc` | 按年份从新到旧 |
| `year_asc` | 按年份从旧到新 |

### 响应

```json
{
  "games": [
    {
      "id": "a3f2c1d8",
      "white": "Carlsen, Magnus",
      "black": "Nepomniachtchi, Ian",
      "white_elo": 2882,
      "black_elo": 2795,
      "avg_elo": 2838,
      "result": "white",
      "year": 2023,
      "event": "WCh 2023"
    }
  ],
  "next_cursor": "WzI4MzgsImEzZjJjMWQ4Il0="
}
```

`next_cursor` 为 `null` 时表示已到最后一页。

### 示例

```bash
# 第一页，按等级分倒序
GET /masters/games?fen=rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR+b+KQkq+-+0+1

# 第二页（传入上次返回的 cursor）
GET /masters/games?fen=...&cursor=WzI4MzgsImEzZjJjMWQ4Il0=

# 按年份从新到旧
GET /masters/games?fen=...&sort=year_desc

# 按年份从旧到新，每页 50 条
GET /masters/games?fen=...&sort=year_asc&limit=50

# 合并棋手：Carlsen 的所有写法一起过滤
GET /masters/games?fen=...&player=Carlsen%2C+M.&player=Carlsen%2C+M..&player=Carlsen%2C+Magnus

# 合并棋手 + 只看该棋手赢的对局
GET /masters/games?fen=...&player=Carlsen%2C+M.&player=Carlsen%2C+M..&player_result=win

# 只看平局
GET /masters/games?fen=...&player=Carlsen%2C+M..&player_result=draw
```

### 前端无限滚动示例

```typescript
let cursor: string | null = null;
let loading = false;

async function loadMore(fen: string, sort: string) {
  if (loading) return;
  loading = true;

  const url = new URL('https://database.catachess.com/masters/games');
  url.searchParams.set('fen', fen);
  url.searchParams.set('sort', sort);
  if (cursor) url.searchParams.set('cursor', cursor);

  const res = await fetch(url);
  const data = await res.json();

  appendGamesToList(data.games);
  cursor = data.next_cursor;   // null = no more pages

  loading = false;
}
```

---

## GET /search/players

棋手名字自动补全。输入前缀，返回匹配的棋手名字列表（按对局数倒序）。

**使用场景**：搜索框 typeahead，让用户选到正确的名字拼写，再传给 `/search/games` 或 `/masters/games`。

### 请求参数

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `q` | string | ✓ | — | 搜索前缀，不区分大小写 |
| `limit` | integer | ✗ | `20` | 最多返回条数（1–50） |

### 响应

```json
{
  "players": [
    { "name": "Carlsen, M.",    "games": 4608 },
    { "name": "Carlsen, M..",   "games": 3066 },
    { "name": "Carlsen, Magnus","games": 9    }
  ]
}
```

### 示例

```bash
GET /search/players?q=Carlsen
GET /search/players?q=Magnus+Car&limit=5
```

---

## GET /search/games

按棋手姓名搜索全部对局，支持多重过滤条件和分页。与局面无关。

### 请求参数

**普通模式**（按棋手前缀搜索）：

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `player` | string | ✓ | — | 棋手姓名前缀，不区分大小写 |
| `color` | string | ✗ | `any` | `white`（执白）/ `black`（执黑）/ `any`（不限） |
| `year_from` | integer | ✗ | null | 年份下限 |
| `year_to` | integer | ✗ | null | 年份上限 |
| `result` | string | ✗ | null | 对局结果（颜色视角）：`white` / `black` / `draw` |
| `white_elo_min` | integer | ✗ | null | 白方等级分下限 |
| `white_elo_max` | integer | ✗ | null | 白方等级分上限 |
| `black_elo_min` | integer | ✗ | null | 黑方等级分下限 |
| `black_elo_max` | integer | ✗ | null | 黑方等级分上限 |
| `sort` | string | ✗ | `elo_desc` | `elo_desc` / `year_desc` / `year_asc` |
| `limit` | integer | ✗ | `20` | 每页数量（1–50） |
| `cursor` | string | ✗ | null | 分页游标 |

**对战模式**（白方 AND 黑方，两个参数同时传即启用）：

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `white` | string | ✗ | null | 白方姓名前缀，与 `black` 同传时启用对战模式 |
| `black` | string | ✗ | null | 黑方姓名前缀，与 `white` 同传时启用对战模式 |

> 对战模式优先级高于 `player + color`。启用后 `player` 参数仍需传入（可传任意非空字符串），`color` 参数被忽略。其余过滤参数（年份、Elo、result、sort、cursor）照常有效。

### 响应

```json
{
  "games": [
    {
      "id": "a3f2c1d8",
      "white": "Carlsen, Magnus",
      "black": "Nepomniachtchi, Ian",
      "white_elo": 2882,
      "black_elo": 2795,
      "avg_elo": 2838,
      "result": "white",
      "year": 2023,
      "event": "WCh 2023"
    }
  ],
  "next_cursor": "WzIwMjMsImEzZjJjMWQ4Il0="
}
```

### 示例

```bash
# 搜索 Carlsen 的所有对局，按等级分倒序
GET /search/games?player=Carlsen%2C+Magnus

# 只看执白的对局
GET /search/games?player=Carlsen%2C+Magnus&color=white

# 2020 年之后，对局结果为白胜
GET /search/games?player=Carlsen%2C+Magnus&year_from=2020&result=white

# 双方等级分均在 2700 以上
GET /search/games?player=Carlsen%2C+Magnus&white_elo_min=2700&black_elo_min=2700

# 按年份从新到旧翻页
GET /search/games?player=Carlsen%2C+Magnus&sort=year_desc&cursor=WzIwMjMsImEzZjJjMWQ4Il0=

# 对战模式：Carlsen 执白 vs Nakamura 执黑
GET /search/games?player=x&white=Carlsen%2C+M..&black=Nakamura%2C+H..

# 对战模式 + 年份过滤
GET /search/games?player=x&white=Carlsen%2C+M..&black=Nakamura%2C+H..&year_from=2020
```

### 前端示例

```typescript
async function searchPlayerGames(options: {
  player: string;
  color?: 'white' | 'black' | 'any';
  yearFrom?: number;
  yearTo?: number;
  result?: 'white' | 'black' | 'draw';
  whiteEloMin?: number;
  whiteEloMax?: number;
  blackEloMin?: number;
  blackEloMax?: number;
  sort?: 'elo_desc' | 'year_desc' | 'year_asc';
  cursor?: string;
}) {
  const url = new URL('https://database.catachess.com/search/games');
  url.searchParams.set('player', options.player);
  if (options.color)       url.searchParams.set('color', options.color);
  if (options.yearFrom)    url.searchParams.set('year_from', String(options.yearFrom));
  if (options.yearTo)      url.searchParams.set('year_to', String(options.yearTo));
  if (options.result)      url.searchParams.set('result', options.result);
  if (options.whiteEloMin) url.searchParams.set('white_elo_min', String(options.whiteEloMin));
  if (options.whiteEloMax) url.searchParams.set('white_elo_max', String(options.whiteEloMax));
  if (options.blackEloMin) url.searchParams.set('black_elo_min', String(options.blackEloMin));
  if (options.blackEloMax) url.searchParams.set('black_elo_max', String(options.blackEloMax));
  if (options.sort)        url.searchParams.set('sort', options.sort);
  if (options.cursor)      url.searchParams.set('cursor', options.cursor);

  const res = await fetch(url);
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json() as Promise<{ games: GameListItem[]; next_cursor: string | null }>;
}
```

---

## GET /lichess

查询 Lichess 在线对局统计，支持按速度和段位过滤。

### 请求参数

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `fen` | string | ✓ | — | 棋盘局面 FEN |
| `play` | string | ✗ | `""` | UCI 走法序列，逗号分隔 |
| `variant` | string | ✗ | `standard` | 棋类变体（目前仅支持 `standard`） |
| `speeds` | string | ✗ | 全部 | 时制过滤，逗号分隔，可选值见下 |
| `ratings` | string | ✗ | 全部 | 段位过滤，逗号分隔，填写段位下限值 |
| `since` | string | ✗ | null | 过滤起始月份，格式 `YYYY-MM`（如 `2023-01`） |
| `until` | string | ✗ | null | 过滤结束月份，格式 `YYYY-MM` |
| `moves` | integer | ✗ | `12` | 返回走法数量上限 |
| `recentGames` | integer | ✗ | `8` | 返回近期对局数量上限（0–8） |

**speeds 可选值**：

| 值 | 说明 | 时长 |
|----|------|------|
| `ultraBullet` | 超闪电 | < 30秒 |
| `bullet` | 闪电 | 30秒–3分钟 |
| `blitz` | 弹幕 | 3–8分钟 |
| `rapid` | 快棋 | 8–25分钟 |
| `classical` | 古典 | > 25分钟 |
| `correspondence` | 通信棋 | 无限制 |

**ratings 可选值**（段位下限）：

`0`, `1000`, `1200`, `1400`, `1600`, `1800`, `2000`, `2200`, `2500`

### 响应

```json
{
  "white": 4521000,
  "draws": 980000,
  "black": 4102000,
  "moves": [
    {
      "uci": "e2e4",
      "san": "e4",
      "white": 2100000,
      "draws": 450000,
      "black": 1900000,
      "averageRating": 1742,
      "game": null
    }
  ],
  "topGames": [],
  "recentGames": [
    {
      "id": "lichess_game_id",
      "white": { "name": "player1", "rating": 2100 },
      "black": { "name": "player2", "rating": 2050 },
      "winner": "black",
      "month": "2024-01"
    }
  ],
  "opening": null
}
```

### 示例

```bash
# 只看快棋和弹幕，1800+ 段位
GET /lichess?fen=...&speeds=blitz,rapid&ratings=1800,2000,2200

# 近 3 个月数据
GET /lichess?fen=...&since=2024-10&until=2025-01
```

---

## GET /player

查询某个玩家的个人开局库。首次查询会触发实时索引，结果以 **NDJSON 流**返回（每行一个 JSON 对象）。

### 请求参数

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `player` | string | ✓ | — | 玩家用户名 |
| `color` | string | ✗ | `white` | 查询执白还是执黑，`white` 或 `black` |
| `fen` | string | ✗ | 起始局面 | 棋盘局面 FEN |
| `play` | string | ✗ | `""` | UCI 走法序列 |
| `speeds` | string | ✗ | 全部 | 同 `/lichess` |
| `since` | string | ✗ | null | 格式 `YYYY-MM` |
| `until` | string | ✗ | null | 格式 `YYYY-MM` |
| `moves` | integer | ✗ | `12` | 返回走法数量上限 |

### 响应（NDJSON 流）

每行一个 JSON 对象，顺序如下：

**第 1 行**：当前已有数据（可能为空）
```json
{"white":0,"draws":0,"black":0,"moves":[],"topGames":[],"recentGames":[],"opening":null}
```

**第 2 行**：队列状态（若需要索引）
```json
{"queuePosition": 0}
```
- `queuePosition: 0` = 正在为你索引
- `queuePosition: 1` = 排队等待中

**第 3 行**：索引完成后的最终结果
```json
{"white":142,"draws":89,"black":61,"moves":[...],"topGames":[],"recentGames":[],"opening":null}
```

若玩家数据已缓存（3小时内索引过），只返回第 1 行（直接给结果）。

### 前端接入示例

```typescript
async function queryPlayer(username: string, color: string, fen: string, play: string) {
  const url = new URL('https://database.catachess.com/player');
  url.searchParams.set('player', username);
  url.searchParams.set('color', color);
  if (fen)  url.searchParams.set('fen', fen);
  if (play) url.searchParams.set('play', play);

  const response = await fetch(url);
  const reader = response.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop()!;
    for (const line of lines) {
      if (!line.trim()) continue;
      const data = JSON.parse(line);
      if ('queuePosition' in data) showLoadingIndicator(data.queuePosition);
      else updateExplorerUI(data);
    }
  }
}
```

---

## GET /game/{id}

查询单局对局的完整元数据与棋谱走法。

### 请求参数

| 参数 | 类型 | 位置 | 说明 |
|------|------|------|------|
| `id` | string | 路径参数 | 8字符对局 ID（来自 `topGames[].id`、`moves[].game.id` 或 `games[].id`） |

### 响应

```json
{
  "id": "a3f2c1d8",
  "white": { "name": "Carlsen, Magnus", "rating": 2882 },
  "black": { "name": "Nepomniachtchi, Ian", "rating": 2795 },
  "winner": "white",
  "year": 2023,
  "month": null,
  "event": "WCh 2023",
  "moves": "e2e4 c5 g1f3 d7d6 d2d4 c5d4 f3d4 g8f6 b1c3 a7a6"
}
```

### 错误

| HTTP 状态码 | 原因 |
|------------|------|
| `404` | ID 不存在 |
| `400` | ID 格式错误 |

---

## GET /health

服务健康检查。

```json
{ "status": "ok" }
```

503 时：
```json
{ "status": "error", "detail": "DB not initialized" }
```

---

## 响应结构参考

### GameListItem（`/masters/games` 和 `/search/games` 返回）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 对局 ID（8字符哈希） |
| `white` | string | 白方姓名 |
| `black` | string | 黑方姓名 |
| `white_elo` | integer \| null | 白方等级分 |
| `black_elo` | integer \| null | 黑方等级分 |
| `avg_elo` | integer \| null | 平均等级分 |
| `result` | `"white"` \| `"black"` \| `"draw"` | 对局结果 |
| `year` | integer \| null | 对局年份 |
| `event` | string \| null | 赛事名称 |

### ExplorerResponse（`/masters` 和 `/lichess` 返回）

| 字段 | 类型 | 说明 |
|------|------|------|
| `white` | integer | 当前局面白胜总局数 |
| `draws` | integer | 当前局面平局总局数 |
| `black` | integer | 当前局面黑胜总局数 |
| `moves` | MoveEntry[] | 候选走法列表，按总局数降序 |
| `topGames` | GameRef[] | 精选对局 |
| `recentGames` | GameRef[] | 近期对局 |
| `opening` | null | 开局名称（预留字段） |

### MoveEntry

| 字段 | 类型 | 说明 |
|------|------|------|
| `uci` | string | UCI 走法，如 `"e2e4"` |
| `san` | string | 标准代数记法，如 `"e4"` |
| `white` | integer | 白胜局数 |
| `draws` | integer | 平局局数 |
| `black` | integer | 黑胜局数 |
| `averageRating` | integer \| null | 平均 Elo |
| `game` | GameRef \| null | 代表性对局 |

### GameRef

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 对局 ID |
| `white` | GamePlayer | 白方 |
| `black` | GamePlayer | 黑方 |
| `winner` | `"white"` \| `"black"` \| null | 胜者 |
| `year` | integer \| null | 年份 |
| `month` | string \| null | 月份 `"YYYY-MM"` |

### GamePlayer

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | string | 姓名 |
| `rating` | integer \| null | Elo |

---

## 错误处理

| HTTP 状态码 | 原因 |
|------------|------|
| `200` | 正常返回（数据为空也返回 200） |
| `400` | 参数错误（FEN 非法、sort 值不合法等） |
| `503` | 数据库未就绪，或 SQLite 索引尚未构建完成 |

空局面正常返回，不报错：
```json
{ "white": 0, "draws": 0, "black": 0, "moves": [], "topGames": [], "recentGames": [], "opening": null }
```

SQLite 未就绪时（索引构建中），`/masters/games` 和 `/search/games` 返回：
```json
{ "detail": "Search index not ready yet. Build in progress." }
```

---

## 前端接入示例（React + TypeScript）

### 类型定义

```typescript
// types/chess.ts

export interface GameListItem {
  id: string;
  white: string;
  black: string;
  white_elo: number | null;
  black_elo: number | null;
  avg_elo: number | null;
  result: 'white' | 'black' | 'draw';
  year: number | null;
  event: string | null;
}

export interface GamesListResponse {
  games: GameListItem[];
  next_cursor: string | null;
}

export type SortOrder = 'elo_desc' | 'year_desc' | 'year_asc';
export type Color = 'white' | 'black' | 'any';
export type GameResult = 'white' | 'black' | 'draw';
export type PlayerResult = 'win' | 'loss' | 'draw';

export interface PlayerSearchFilters {
  color?: Color;
  yearFrom?: number;
  yearTo?: number;
  result?: GameResult;
  whiteEloMin?: number;
  whiteEloMax?: number;
  blackEloMin?: number;
  blackEloMax?: number;
  sort?: SortOrder;
  // 对战模式：同时传 white 和 black 即启用（优先级高于 color）
  white?: string;
  black?: string;
}

export interface PositionGamesFilters {
  players?: string[];        // 合并棋手，来自 /search/players
  playerResult?: PlayerResult; // 棋手视角胜负，需同时传 players
  sort?: SortOrder;
}
```

---

### API 客户端

```typescript
// lib/api.ts

const BASE = 'https://database.catachess.com';

export async function fetchMastersGames(
  fen: string,
  sort: SortOrder,
  players: string[] = [],
  playerResult?: PlayerResult,
  cursor?: string | null,
): Promise<GamesListResponse> {
  const url = new URL(`${BASE}/masters/games`);
  url.searchParams.set('fen', fen);
  url.searchParams.set('sort', sort);
  players.forEach(p => url.searchParams.append('player', p)); // append，不是 set
  if (playerResult) url.searchParams.set('player_result', playerResult);
  if (cursor)       url.searchParams.set('cursor', cursor);

  const res = await fetch(url);
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json();
}

export async function fetchPlayerGames(
  player: string,
  filters: PlayerSearchFilters,
  cursor?: string | null,
): Promise<GamesListResponse> {
  const url = new URL(`${BASE}/search/games`);
  url.searchParams.set('player', player);

  // 对战模式：white + black 同时存在时后端忽略 color，直接 AND 匹配
  if (filters.white)        url.searchParams.set('white', filters.white);
  if (filters.black)        url.searchParams.set('black', filters.black);

  if (filters.color)        url.searchParams.set('color', filters.color);
  if (filters.yearFrom)     url.searchParams.set('year_from', String(filters.yearFrom));
  if (filters.yearTo)       url.searchParams.set('year_to', String(filters.yearTo));
  if (filters.result)       url.searchParams.set('result', filters.result);
  if (filters.whiteEloMin)  url.searchParams.set('white_elo_min', String(filters.whiteEloMin));
  if (filters.whiteEloMax)  url.searchParams.set('white_elo_max', String(filters.whiteEloMax));
  if (filters.blackEloMin)  url.searchParams.set('black_elo_min', String(filters.blackEloMin));
  if (filters.blackEloMax)  url.searchParams.set('black_elo_max', String(filters.blackEloMax));
  if (filters.sort)         url.searchParams.set('sort', filters.sort);
  if (cursor)               url.searchParams.set('cursor', cursor);

  const res = await fetch(url);
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json();
}
```

---

### Hook：开局探索器对局列表（无限滚动）

用于"给定局面，展示全部对局"场景，支持切换排序方式。

```typescript
// hooks/useMastersGames.ts
import { useState, useEffect, useCallback, useRef } from 'react';
import { fetchMastersGames } from '../lib/api';

export function useMastersGames(fen: string, sort: SortOrder) {
  const [games, setGames] = useState<GameListItem[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 切换局面或排序时重置
  useEffect(() => {
    setGames([]);
    setCursor(null);
    setHasMore(true);
    setError(null);
  }, [fen, sort]);

  const loadMore = useCallback(async () => {
    if (loading || !hasMore) return;
    setLoading(true);
    setError(null);
    try {
      const data = await fetchMastersGames(fen, sort, cursor);
      setGames(prev => [...prev, ...data.games]);
      setCursor(data.next_cursor);
      setHasMore(data.next_cursor !== null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, [fen, sort, cursor, loading, hasMore]);

  // 首次加载
  const initialized = useRef(false);
  useEffect(() => {
    initialized.current = false;
  }, [fen, sort]);
  useEffect(() => {
    if (!initialized.current) {
      initialized.current = true;
      loadMore();
    }
  }, [fen, sort]); // eslint-disable-line

  return { games, loading, error, hasMore, loadMore };
}
```

**使用示例：**

```tsx
// components/PositionGameList.tsx
import { useRef, useCallback } from 'react';
import { useMastersGames } from '../hooks/useMastersGames';

const SORT_LABELS = {
  elo_desc:  '等级分（高→低）',
  year_desc: '时间（新→旧）',
  year_asc:  '时间（旧→新）',
} as const;

export function PositionGameList({ fen }: { fen: string }) {
  const [sort, setSort] = useState<SortOrder>('elo_desc');
  const { games, loading, error, hasMore, loadMore } = useMastersGames(fen, sort);

  // IntersectionObserver 触发加载
  const observerRef = useRef<IntersectionObserver | null>(null);
  const sentinelRef = useCallback((node: HTMLDivElement | null) => {
    if (observerRef.current) observerRef.current.disconnect();
    if (!node) return;
    observerRef.current = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting) loadMore();
    });
    observerRef.current.observe(node);
  }, [loadMore]);

  return (
    <div>
      {/* 排序选择 */}
      <div className="sort-tabs">
        {(Object.keys(SORT_LABELS) as SortOrder[]).map(s => (
          <button
            key={s}
            className={sort === s ? 'active' : ''}
            onClick={() => setSort(s)}
          >
            {SORT_LABELS[s]}
          </button>
        ))}
      </div>

      {/* 对局列表 */}
      <div className="game-list">
        {games.map(game => (
          <GameRow key={game.id} game={game} />
        ))}
      </div>

      {/* 滚动触发点 */}
      {hasMore && <div ref={sentinelRef} style={{ height: 1 }} />}
      {loading && <div className="loading">加载中…</div>}
      {error && <div className="error">{error}</div>}
      {!hasMore && games.length > 0 && (
        <div className="end">共 {games.length} 局</div>
      )}
    </div>
  );
}

function GameRow({ game }: { game: GameListItem }) {
  const resultColor = { white: '#4caf50', black: '#333', draw: '#888' };
  return (
    <div className="game-row">
      <span className="players">
        {game.white} ({game.white_elo ?? '?'}) vs {game.black} ({game.black_elo ?? '?'})
      </span>
      <span className="result" style={{ color: resultColor[game.result] }}>
        {game.result === 'white' ? '1-0' : game.result === 'black' ? '0-1' : '½-½'}
      </span>
      <span className="meta">{game.year} · {game.event ?? '—'}</span>
    </div>
  );
}
```

---

### Hook：棋手检索（带过滤器 + 无限滚动）

```typescript
// hooks/usePlayerSearch.ts
import { useState, useEffect, useCallback } from 'react';
import { fetchPlayerGames } from '../lib/api';

export function usePlayerSearch(player: string, filters: PlayerSearchFilters) {
  const [games, setGames] = useState<GameListItem[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 任何参数变化时重置并重新搜索
  useEffect(() => {
    if (!player.trim()) {
      setGames([]);
      setHasMore(false);
      return;
    }
    setGames([]);
    setCursor(null);
    setHasMore(false);
    setError(null);

    let cancelled = false;
    setLoading(true);
    fetchPlayerGames(player, filters, null)
      .then(data => {
        if (cancelled) return;
        setGames(data.games);
        setCursor(data.next_cursor);
        setHasMore(data.next_cursor !== null);
      })
      .catch(e => {
        if (!cancelled) setError(e.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => { cancelled = true; };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [player, JSON.stringify(filters)]);

  const loadMore = useCallback(async () => {
    if (loading || !hasMore || !cursor) return;
    setLoading(true);
    try {
      const data = await fetchPlayerGames(player, filters, cursor);
      setGames(prev => [...prev, ...data.games]);
      setCursor(data.next_cursor);
      setHasMore(data.next_cursor !== null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, [player, filters, cursor, loading, hasMore]);

  return { games, loading, error, hasMore, loadMore };
}
```

**使用示例：**

```tsx
// components/PlayerSearch.tsx
import { useState, useRef, useCallback } from 'react';
import { usePlayerSearch } from '../hooks/usePlayerSearch';

export function PlayerSearch() {
  const [input, setInput]     = useState('');
  const [player, setPlayer]   = useState('');
  const [color, setColor]     = useState<Color>('any');
  const [yearFrom, setYearFrom] = useState('');
  const [yearTo, setYearTo]   = useState('');
  const [result, setResult]   = useState('');
  const [sort, setSort]       = useState<SortOrder>('elo_desc');

  const filters: PlayerSearchFilters = {
    color,
    sort,
    yearFrom:  yearFrom  ? Number(yearFrom)  : undefined,
    yearTo:    yearTo    ? Number(yearTo)    : undefined,
    result:    result    ? result as GameResult : undefined,
  };

  const { games, loading, error, hasMore, loadMore } =
    usePlayerSearch(player, filters);

  // 无限滚动
  const observerRef = useRef<IntersectionObserver | null>(null);
  const sentinelRef = useCallback((node: HTMLDivElement | null) => {
    if (observerRef.current) observerRef.current.disconnect();
    if (!node) return;
    observerRef.current = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting) loadMore();
    });
    observerRef.current.observe(node);
  }, [loadMore]);

  return (
    <div>
      {/* 搜索框 */}
      <form onSubmit={e => { e.preventDefault(); setPlayer(input.trim()); }}>
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="棋手姓名，如 Carlsen, Magnus"
        />
        <button type="submit">搜索</button>
      </form>

      {/* 过滤器 */}
      <div className="filters">
        <select value={color} onChange={e => setColor(e.target.value as Color)}>
          <option value="any">全部颜色</option>
          <option value="white">执白</option>
          <option value="black">执黑</option>
        </select>

        <select value={result} onChange={e => setResult(e.target.value)}>
          <option value="">全部结果</option>
          <option value="white">白胜</option>
          <option value="black">黑胜</option>
          <option value="draw">平局</option>
        </select>

        <input
          type="number" placeholder="起始年份"
          value={yearFrom} onChange={e => setYearFrom(e.target.value)}
        />
        <input
          type="number" placeholder="结束年份"
          value={yearTo} onChange={e => setYearTo(e.target.value)}
        />

        <select value={sort} onChange={e => setSort(e.target.value as SortOrder)}>
          <option value="elo_desc">等级分（高→低）</option>
          <option value="year_desc">时间（新→旧）</option>
          <option value="year_asc">时间（旧→新）</option>
        </select>
      </div>

      {/* 结果列表 */}
      {games.length > 0 && (
        <div className="game-list">
          {games.map(game => (
            <div key={game.id} className="game-row">
              <span>{game.white} ({game.white_elo ?? '?'})</span>
              <span className="vs">vs</span>
              <span>{game.black} ({game.black_elo ?? '?'})</span>
              <span className="result">
                {game.result === 'white' ? '1-0' : game.result === 'black' ? '0-1' : '½-½'}
              </span>
              <span className="meta">{game.year} · {game.event ?? '—'}</span>
            </div>
          ))}
          {hasMore && <div ref={sentinelRef} style={{ height: 1 }} />}
        </div>
      )}

      {loading && <div className="loading">加载中…</div>}
      {error   && <div className="error">{error}</div>}
      {!loading && !hasMore && games.length > 0 && (
        <div className="end">共 {games.length} 局</div>
      )}
      {!loading && player && games.length === 0 && (
        <div className="empty">未找到对局</div>
      )}
    </div>
  );
}
```

---

## 数据规模

| 数据库 | 对局数 | 来源 | 时间跨度 |
|--------|--------|------|----------|
| Masters | **460 万局** | TWIC（世界棋坛锦标赛） | 1995–2026 |
| Lichess | 待导入 | — | — |
| Player | 按需索引 | 本地 PGN | — |

每局棋重演全部走法，每个局面按 Zobrist 哈希索引入 RocksDB 和 SQLite。