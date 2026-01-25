# Stage 05 - 后端 API 与服务层

目标：落地 API + 服务编排层，保证可调用。

## 一、API 功能点
- 创建/获取 player profile
- 上传 PGN（保存到 R2 + 进入处理队列）
- 查询统计（白/黑/总）
- 导出统计（CSV/JSON）
- 查询上传状态与失败列表

## 二、服务层职责
- 接收上传 → 写 R2 → 创建 upload 记录
- 触发解析 pipeline
- 写入统计与失败记录
- 返回进度与状态

## 三、失败盘记录结构（必须固定）
- game_index
- headers（White/Black/Date/Event/Result）
- player_color
- move_count
- error_code
- error_message
- retry_count
- last_attempt_at

## 四、error_code 枚举（必须固定）
- INVALID_PGN
- HEADER_MISSING
- MATCH_AMBIGUOUS
- ENGINE_TIMEOUT
- ENGINE_503
- ILLEGAL_MOVE
- UNKNOWN_ERROR

## 五、API 返回字段（最小集）
- status
- processed_positions
- failed_games_count
- last_updated
- needs_confirmation
- match_candidates

## 六、导出 API 参数（范围控制）
- upload_ids（可选，逗号分隔）
- from / to（可选，ISO 时间）

## Checklist
- [x] API 路径对齐
- [x] 服务层职责清晰
- [x] 返回字段最小集合确认
