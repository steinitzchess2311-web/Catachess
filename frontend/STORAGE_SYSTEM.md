# Chessboard Auto-Save Storage System

## 概述

✅ 已实现完整的自动保存系统

### 架构原则

⚠️ **重要：前端只负责触发保存事件，所有逻辑在后端**

#### 前端职责
- 每走一步棋时触发保存事件
- 提供评注和标记的 UI
- 显示游戏历史

#### 后端职责
- 生成带变化分支的 PGN（如 `1.e4 (1.d4 Nf6 2.c4) e5`）
- 处理变化分支的逻辑
- 存储到 R2 数据库
- 管理游戏状态

## 已实现的功能

### 1. 自动保存系统

```typescript
const chessboard = createChessboard(container, {
  enableStorage: true,  // 启用自动保存
  gameId: 'game_123',   // 游戏 ID
  onMove: (move) => {
    // 每一步棋都会自动保存到后端
  },
  onSaved: (gameId) => {
    console.log('已保存:', gameId);
  },
});
```

**工作流程：**
1. 用户走一步棋
2. 前端验证走法（调用后端）
3. 前端应用走法
4. 前端触发保存事件 → 后端
5. 后端生成/更新 PGN
6. 后端存储到 R2

### 2. 变化分支支持

```typescript
const storage = chessboard.getStorage();

// 开始新的变化分支
await storage.startVariation(parentMoveId);

// 在变化分支中走棋
await storage.saveMove({
  gameId: 'game_123',
  move: alternativeMove,
  position: position,
  isVariation: true,
  parentMoveId: parentMoveId,
});

// 结束变化分支
await storage.endVariation();

// 后端生成 PGN：
// 1. e4 (1. d4 Nf6 2. c4 e6) e5 2. Nf3
```

### 3. 评注和标记

```typescript
// 添加评注
await chessboard.addComment('好棋！');

// 添加标记（NAG）
await chessboard.addNAG(1);  // ! 好棋
await chessboard.addNAG(2);  // ? 失误
await chessboard.addNAG(3);  // !! 妙手
await chessboard.addNAG(4);  // ?? 致命失误
```

### 4. 导出 PGN

```typescript
// 从后端获取完整的 PGN
const pgn = await chessboard.getPGN();

console.log(pgn);
// 输出:
// [Event "Casual Game"]
// [Site "Catachess"]
// [Date "2026.01.12"]
// ...
// 1. e4 e5 2. Nf3 ! (2...d6 { Philidor Defense }) Nc6 *
```

## 后端需要实现的 API

### 1. 保存走法
```
POST /api/games/save-move

请求体:
{
  "game_id": "game_123",
  "move": {
    "from": { "file": 4, "rank": 1 },
    "to": { "file": 4, "rank": 3 }
  },
  "position_fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
  "is_variation": false,
  "parent_move_id": null,
  "comment": null,
  "nag": null,
  "move_number": 1
}

后端处理:
1. 使用 chess_basic.pgn.vari.writer.PGNWriterVari
2. 调用 add_move() 添加走法
3. 如果是变化分支，使用 start_variation() / end_variation()
4. 生成 PGN 字符串
5. 存储到 R2 数据库
6. 返回成功

返回:
{
  "success": true,
  "move_id": "move_42",
  "pgn_preview": "1. e4 e5 2. Nf3..."
}
```

### 2. 开始变化分支
```
POST /api/games/start-variation

请求体:
{
  "game_id": "game_123",
  "parent_move_id": "move_5"
}

后端处理:
1. 定位到父走法
2. 调用 PGNWriterVari.start_variation()
3. 标记当前状态为变化分支起点

返回:
{
  "success": true,
  "variation_id": "var_1"
}
```

### 3. 结束变化分支
```
POST /api/games/end-variation

请求体:
{
  "game_id": "game_123"
}

后端处理:
1. 调用 PGNWriterVari.end_variation()
2. 返回主线

返回:
{
  "success": true
}
```

### 4. 添加评注
```
POST /api/games/add-comment

请求体:
{
  "game_id": "game_123",
  "move_id": "move_5",  // 可选，默认最后一步
  "comment": "好棋！"
}

后端处理:
1. 调用 PGNWriterVari.add_comment()
2. 更新 PGN

返回:
{
  "success": true
}
```

### 5. 添加标记（NAG）
```
POST /api/games/add-nag

请求体:
{
  "game_id": "game_123",
  "move_id": "move_5",
  "nag": 1  // 1=!, 2=?, 3=!!, 4=??, etc.
}

后端处理:
1. 调用 PGNWriterVari.add_nag()
2. 更新 PGN

返回:
{
  "success": true
}
```

### 6. 获取 PGN
```
GET /api/games/{game_id}/pgn

后端处理:
1. 从内存或 R2 加载游戏
2. 调用 PGNWriterVari.to_pgn_string()
3. 返回完整 PGN

返回:
{
  "pgn": "[Event \"Casual Game\"]\n[Site \"Catachess\"]...",
  "game_id": "game_123",
  "move_count": 42
}
```

### 7. 加载游戏
```
GET /api/games/{game_id}

后端处理:
1. 从 R2 加载游戏 PGN
2. 解析游戏状态
3. 返回游戏信息

返回:
{
  "game_id": "game_123",
  "pgn": "...",
  "move_count": 42,
  "current_position": "r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3",
  "player_white": "Player 1",
  "player_black": "Player 2",
  "result": "*"
}
```

### 8. 删除游戏
```
DELETE /api/games/{game_id}

后端处理:
1. 从 R2 删除游戏文件
2. 清除数据库记录

返回:
{
  "success": true
}
```

## 后端实现参考

### 使用现有的 PGN 模块

后端已有完整的 PGN 系统：

```python
from core.chess_basic.pgn.vari.writer import PGNWriterVari
from core.chess_basic.types import Move, BoardState

# 创建 PGN 写入器（支持变化分支）
writer = PGNWriterVari()

# 添加走法
move = Move(from_square=..., to_square=...)
writer.add_move(move, state_before, san="e4")

# 开始变化分支
writer.start_variation()
writer.add_move(alternative_move, state, san="d4")
writer.add_comment("Philidor Defense")
writer.end_variation()

# 继续主线
writer.add_move(next_move, state, san="e5")

# 生成 PGN
pgn_string = writer.to_pgn_string()
# 输出: "1. e4 (1. d4 { Philidor Defense }) e5 *"
```

### R2 存储结构

```
Bucket: catachess-games
路径: /games/{user_id}/{game_id}.pgn

文件内容:
[Event "Casual Game"]
[Site "Catachess"]
[Date "2026.01.12"]
[White "Player 1"]
[Black "Player 2"]
[Result "*"]

1. e4 e5 2. Nf3 (2...d6 { Philidor Defense }) Nc6 *
```

### 数据库记录（可选）

```sql
CREATE TABLE games (
  game_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  player_white TEXT,
  player_black TEXT,
  event TEXT,
  site TEXT,
  date DATE,
  result TEXT,
  move_count INTEGER,
  r2_path TEXT,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

## NAG 标记对照表

| NAG | 符号 | 含义 |
|-----|------|------|
| 1   | !    | 好棋 |
| 2   | ?    | 失误 |
| 3   | !!   | 妙手 |
| 4   | ??   | 致命失误 |
| 5   | !?   | 有趣的着法 |
| 6   | ?!   | 可疑的着法 |
| 10  | =    | 均势 |
| 13  | ∞    | 不明朗 |
| 14  | ⩲    | 白方稍优 |
| 15  | ⩱    | 黑方稍优 |

## 完整示例

### 前端代码

```typescript
import { createChessboard } from './ui/modules/chessboard';

const chessboard = createChessboard(container, {
  enableStorage: true,
  gameId: 'game_123',
  onSaved: (gameId) => {
    console.log('自动保存成功:', gameId);
  },
});

// 用户走棋 → 自动保存
// 每一步都会调用 POST /api/games/save-move
```

### 后端代码（伪代码）

```python
@router.post("/api/games/save-move")
async def save_move(request: SaveMoveRequest):
    # 1. 加载或创建游戏
    game = load_game(request.game_id) or create_game(request.game_id)

    # 2. 添加走法到 PGN 写入器
    writer = game.pgn_writer  # PGNWriterVari 实例

    if request.is_variation:
        # 如果是变化分支中的走法，确保已开始变化
        pass

    # 添加走法
    writer.add_move(
        move=parse_move(request.move),
        state_before=parse_fen(request.position_fen),
        san=calculate_san(request.move, request.position_fen)
    )

    # 添加评注/标记
    if request.comment:
        writer.add_comment(request.comment)
    if request.nag:
        writer.add_nag(request.nag)

    # 3. 生成 PGN
    pgn_string = writer.to_pgn_string()

    # 4. 存储到 R2
    r2_client.put_object(
        Bucket='catachess-games',
        Key=f'games/{user_id}/{request.game_id}.pgn',
        Body=pgn_string.encode('utf-8')
    )

    # 5. 更新数据库
    db.execute(
        "UPDATE games SET move_count = ?, updated_at = ? WHERE game_id = ?",
        (request.move_number, datetime.now(), request.game_id)
    )

    return {
        "success": True,
        "move_id": f"move_{request.move_number}",
        "pgn_preview": pgn_string[:100] + "..."
    }
```

## 性能优化

### 1. 批量保存
可以累积多步后一次性保存，减少 API 调用：

```typescript
const storage = chessboard.getStorage();
storage.setAutoSave(false);  // 禁用自动保存

// 手动批量保存
for (const move of moves) {
  await storage.saveMove({ ... });
}
```

### 2. 本地缓存
前端可以缓存 PGN，定期同步到后端：

```typescript
// 存储到 localStorage
localStorage.setItem(`game_${gameId}`, await chessboard.getPGN());
```

### 3. 压缩
对于大型游戏（200+ 步），可以压缩 PGN：

```python
import gzip

# 压缩 PGN
compressed = gzip.compress(pgn_string.encode('utf-8'))

# 存储到 R2
r2_client.put_object(
    Bucket='catachess-games',
    Key=f'games/{user_id}/{game_id}.pgn.gz',
    Body=compressed
)
```

## 错误处理

```typescript
const chessboard = createChessboard(container, {
  enableStorage: true,
  onStorageError: (error) => {
    // 保存失败时的处理
    console.error('保存失败:', error);

    // 显示通知
    showNotification('无法保存游戏，请检查网络连接', 'error');

    // 可以实现重试逻辑
    setTimeout(() => {
      chessboard.getStorage()?.saveMove({ ... });
    }, 3000);
  },
});
```

## 总结

✅ **前端已完成：**
1. GameStorage 类 - 触发后端保存
2. 自动保存集成到 Chessboard
3. 变化分支支持
4. 评注和标记支持
5. PGN 导出
6. 完整的示例代码

⏳ **后端需要实现：**
1. 8 个 API 端点（保存、变化、评注等）
2. 使用现有的 `chess_basic.pgn.vari.writer`
3. R2 存储集成
4. 游戏状态管理

🎯 **核心原则：**
- 前端只触发事件
- 后端处理所有逻辑
- R2 存储所有数据
