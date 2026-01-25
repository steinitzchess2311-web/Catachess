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
- game_index\n- headers（White/Black/Date/Event/Result）\n- player_color\n- move_count\n- error_code\n- error_message\n- retry_count\n- last_attempt_at

## 四、API 返回字段（最小集）
- status
- processed_positions
- failed_games_count
- last_updated

## Checklist
- [ ] API 路径对齐
- [ ] 服务层职责清晰
- [ ] 返回字段最小集合确认
