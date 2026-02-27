# Opening Trainer — 数据库设计

## 核心思路

进度以**棋步粒度**存储：key 是 `(user_id, from_fen, move_san, color)`。

不绑定 study_id，也不绑定 chapter。原因：Opening Trainer 的核心操作是"合并"——同一个 study 下多个 chapters 先合并成一棵大树，再拆分成训练单元。两个 chapter 可能经过不同路径到达同一个局面（转置），合并后是同一个节点。进度自然应该跟着**局面**走，而不是跟着 chapter 或 study 走。

这样做的好处：
- 同一局面无论从哪个 chapter 到达，进度共享，不重复练习
- 用户修改 study（增删章节）不会丢失已有进度
- 将来支持跨 study 合并也不需要改表结构

---

## 新建表：`opening_trainer_moves`

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUID / serial | 主键 |
| `user_id` | FK → users | 哪个用户 |
| `from_fen` | text | 走棋**前**的局面 FEN（稳定的位置 key） |
| `move_san` | text | 正确走法（SAN 格式） |
| `color` | enum('white','black') | 用户练习的视角 |
| `correct_count` | int default 0 | 历史答对总次数 |
| `wrong_count` | int default 0 | 历史答错总次数 |
| `consecutive_correct` | int default 0 | 当前连对次数（用于3连对机制） |
| `mastered` | bool default false | 是否已掌握（连对3次后置 true） |
| `last_practiced_at` | timestamp | 最近一次练习时间 |

**唯一索引**：`(user_id, from_fen, move_san, color)`

---

## 3连对掌握机制

```
用户答对：
  consecutive_correct += 1
  correct_count += 1
  if consecutive_correct >= 3:
    mastered = true

用户答错：
  consecutive_correct = 0
  wrong_count += 1
  mastered = false（如果之前已掌握，重新标为未掌握）
```

---

## 练习时的跳过逻辑

进入一个训练单元时，系统遍历该单元内所有需要用户走的棋步：
- `mastered = true` → 直接跳过（快速带过，不要求用户输入）
- `mastered = false` → 正常练习

这样已经掌握的线会被快速略过，用户只需专注于还没掌握的部分。（参考 Chessable 的 review 模式）

---

## 将来扩展：间隔重复（Spaced Repetition）

目前不实现，但表结构预留扩展空间。将来可参考 SM-2 算法（Anki/Chessdriller 均使用此算法）增加以下字段：

| 字段 | 说明 |
|------|------|
| `review_due_at` | 下次复习时间 |
| `review_interval` | SM-2 间隔（天） |
| `review_ease` | SM-2 ease factor |

届时"已掌握"的棋步不是永久跳过，而是按照遗忘曲线安排复习时间。

---

## API 端点（待实现）

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/v1/opening-trainer/progress?fens[]=...&color=white` | 批量查询一组局面的进度 |
| `POST` | `/api/v1/opening-trainer/progress` | 记录一次练习结果（对/错） |

POST body：
```json
{
  "from_fen": "rnbqkbnr/pppppppp/...",
  "move_san": "e4",
  "color": "white",
  "correct": true
}
```

---

## 参考
- [Chessdriller](https://github.com/gtim/chessdriller)（开源，Prisma schema，SM-2 实现参考）
