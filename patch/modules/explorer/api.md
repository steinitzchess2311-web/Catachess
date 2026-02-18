base url: database.catachess.com

所有接口均为 `GET` 请求，返回 `application/json`（`/player` 除外，返回 NDJSON 流）。
无需鉴权，支持跨域（CORS 全开放）。

---

## 目录

- [通用说明](#通用说明)
- [GET /masters](#get-masters)
- [GET /lichess](#get-lichess)
- [GET /player](#get-player)
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

# 指定年份范围
GET /masters?fen=...&since=2015&until=2020
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

# 子弹棋，所有段位，1.e4 之后
GET /lichess?fen=...&play=e2e4&speeds=bullet
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

**第 3 行**：索引完成后的最终结果（格式同第 1 行）
```json
{"white":142,"draws":89,"black":61,"moves":[...],"topGames":[],"recentGames":[],"opening":null}
```

若玩家数据已缓存（3小时内索引过），只返回 **第 1 行**（直接给结果）。

### 前端接入示例（fetch + ReadableStream）

```javascript
async function queryPlayer(username, color, fen, play) {
  const url = new URL('https://database.catachess.com/player');
  url.searchParams.set('player', username);
  url.searchParams.set('color', color);
  if (fen) url.searchParams.set('fen', fen);
  if (play) url.searchParams.set('play', play);

  const response = await fetch(url);
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop(); // 保留未完成的行

    for (const line of lines) {
      if (!line.trim()) continue;
      const data = JSON.parse(line);

      if ('queuePosition' in data) {
        // 显示加载状态
        showLoadingIndicator(data.queuePosition);
      } else {
        // 更新开局数据展示
        updateExplorerUI(data);
      }
    }
  }
}
```

---

## GET /health

服务健康检查。

### 响应

```json
{ "status": "ok" }
```

503 时：
```json
{ "status": "error", "detail": "DB not initialized" }
```

---

## 响应结构参考

### ExplorerResponse

| 字段 | 类型 | 说明 |
|------|------|------|
| `white` | integer | 当前局面白胜总局数 |
| `draws` | integer | 当前局面平局总局数 |
| `black` | integer | 当前局面黑胜总局数 |
| `moves` | MoveEntry[] | 候选走法列表，按总局数降序排列 |
| `topGames` | GameRef[] | 精选对局（masters）|
| `recentGames` | GameRef[] | 近期对局（lichess/player）|
| `opening` | null | 开局名称（暂未实现，预留字段）|

### MoveEntry

| 字段 | 类型 | 说明 |
|------|------|------|
| `uci` | string | UCI 格式走法，如 `"e2e4"` |
| `san` | string | 标准代数记法，如 `"e4"` |
| `white` | integer | 这步走法后白胜局数 |
| `draws` | integer | 这步走法后平局局数 |
| `black` | integer | 这步走法后黑胜局数 |
| `averageRating` | integer \| null | 走法对局的平均 Elo |
| `game` | GameRef \| null | 代表性精选对局（masters 模式） |

### GameRef

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 对局 ID（8字符哈希） |
| `white` | GamePlayer | 白方信息 |
| `black` | GamePlayer | 黑方信息 |
| `winner` | `"white"` \| `"black"` \| null | 胜者，null 为平局 |
| `year` | integer \| null | 对局年份（masters） |
| `month` | string \| null | 对局月份 `"YYYY-MM"`（lichess/player）|

### GamePlayer

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | string | 玩家姓名/用户名 |
| `rating` | integer \| null | Elo 评分 |

---

## 错误处理

| HTTP 状态码 | 原因 |
|------------|------|
| `200` | 正常返回（即使数据为空，也返回 200 + 空 moves 数组）|
| `400` | 参数错误（FEN 非法、UCI 走法无效等）|
| `503` | 数据库未就绪 |

**400 示例响应**：
```json
{ "detail": "Invalid UCI move 'e2e9': illegal move" }
```

空局面（未被收录）正常返回，不报错：
```json
{ "white": 0, "draws": 0, "black": 0, "moves": [], "topGames": [], "recentGames": [], "opening": null }
```

---

## 前端接入示例

### JavaScript / TypeScript

```typescript
const BASE = 'https://database.catachess.com';

// 查询 Masters 开局
async function getMasters(fen: string, play: string = '', options?: {
  since?: number;
  until?: number;
  moves?: number;
}) {
  const url = new URL(`${BASE}/masters`);
  url.searchParams.set('fen', fen);
  if (play) url.searchParams.set('play', play);
  if (options?.since) url.searchParams.set('since', String(options.since));
  if (options?.until) url.searchParams.set('until', String(options.until));
  if (options?.moves) url.searchParams.set('moves', String(options.moves));

  const res = await fetch(url);
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json();
}

// 查询 Lichess 开局
async function getLichess(fen: string, play: string = '', options?: {
  speeds?: string[];
  ratings?: number[];
  since?: string;  // "YYYY-MM"
  until?: string;
}) {
  const url = new URL(`${BASE}/lichess`);
  url.searchParams.set('fen', fen);
  if (play) url.searchParams.set('play', play);
  if (options?.speeds?.length) url.searchParams.set('speeds', options.speeds.join(','));
  if (options?.ratings?.length) url.searchParams.set('ratings', options.ratings.join(','));
  if (options?.since) url.searchParams.set('since', options.since);
  if (options?.until) url.searchParams.set('until', options.until);

  const res = await fetch(url);
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json();
}

// 计算胜率（方便展示进度条）
function winRate(data: { white: number; draws: number; black: number }) {
  const total = data.white + data.draws + data.black;
  if (total === 0) return { white: 0, draw: 0, black: 0 };
  return {
    white: (data.white / total * 100).toFixed(1),
    draw: (data.draws / total * 100).toFixed(1),
    black: (data.black / total * 100).toFixed(1),
  };
}
```

### 典型用法：棋盘联动

```typescript
// 用户落子后，更新开局探索器
async function onMove(history: string[]) {
  const startFen = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1';
  const play = history.join(',');  // ['e2e4', 'e7e5', 'g1f3']

  const data = await getMasters(startFen, play, { moves: 10 });
  // data.moves 按热度排序，直接渲染
}
```

---

## 数据规模

| 数据库 | 对局数 | 来源 | 时间跨度 |
|--------|--------|------|----------|
| Masters | **460 万局** | TWIC（世界棋坛锦标赛） | 1995–2026 |
| Lichess | 待导入 | — | — |
| Player | 按需索引 | 本地 PGN | — |

每局棋重演前 **50 步**，每个局面按 Zobrist 哈希索引入 RocksDB。