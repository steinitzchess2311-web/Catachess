# Stage 05 Summary - 后端 API 与服务层

## 完成内容

### 1. API 功能点（对齐 Stage 02）
| 功能 | 对应 API |
|------|----------|
| 创建/获取 player profile | POST/GET /api/tagger/players |
| 上传 PGN | POST /api/tagger/players/:id/uploads |
| 查询统计 | GET /api/tagger/players/:id/stats |
| 导出统计 | GET /api/tagger/players/:id/exports |
| 查询状态/失败列表 | GET /api/tagger/players/:id |

### 2. 服务层职责
1. 接收上传 → 写 R2 → 创建 upload 记录
2. 触发解析 pipeline
3. 写入统计与失败记录
4. 返回进度与状态

### 3. 失败盘记录结构（已固定）
- game_index, headers, player_color, move_count
- error_code, error_message, retry_count, last_attempt_at

### 4. error_code 枚举（已固定）
| 错误码 | 含义 |
|--------|------|
| INVALID_PGN | PGN 格式无效 |
| HEADER_MISSING | 缺少必要 header |
| MATCH_AMBIGUOUS | 匹配不唯一 |
| ENGINE_TIMEOUT | 引擎超时 |
| ENGINE_503 | 引擎服务不可用 |
| ILLEGAL_MOVE | 非法走子 |
| UNKNOWN_ERROR | 未知错误 |

### 5. API 返回字段最小集
- status, processed_positions, failed_games_count
- last_updated, needs_confirmation, match_candidates

### 6. 导出 API 参数
- upload_ids（可选，逗号分隔）
- from / to（可选，ISO 时间）

## Checklist 完成状态
- [x] API 路径对齐
- [x] 服务层职责清晰
- [x] 返回字段最小集合确认

## 下一步
进入 Stage 06：Pipeline 实现（PGN → tag）
