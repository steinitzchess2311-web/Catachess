# Stage 04 - Postgres 表结构与索引

目标：定义数据库结构与索引策略。

## 一、表结构

### 1) player_profiles
- id (uuid, pk)
- display_name
- normalized_name
- aliases (text[])
- created_at / updated_at

### 2) pgn_uploads
- id (uuid, pk)
- player_id (fk)
- r2_key_raw
- checksum
- status
- checkpoint_state (jsonb)
- created_at / updated_at

### 3) pgn_games
- id (uuid, pk)
- player_id (fk)
- upload_id (fk)
- game_hash
- white_name / black_name
- player_color (white/black)
- game_result
- move_count

### 4) failed_games
- id (uuid, pk)
- player_id (fk)
- upload_id (fk)
- game_hash
- game_index
- headers (jsonb)
- player_color
- move_count
- error_code
- error_message
- retry_count
- last_attempt_at

### 5) tag_stats
- player_id (fk)
- scope (white/black/total)
- tag_name
- tag_count
- total_positions
- engine_version
- depth
- multipv
- stats_version
- updated_at

### 6) tag_runs (可选)
- id (uuid)
- player_id
- engine_version
- depth / multipv
- processed_positions
- started_at / finished_at

## 二、索引与约束
- pgn_games: unique(player_id, game_hash)
- pgn_games: index(upload_id)
- tag_stats: index(player_id, scope)
- tag_stats: unique(player_id, scope, tag_name, stats_version, engine_version, depth, multipv)
- failed_games: index(player_id, upload_id)

## Checklist
- [x] 表结构字段确认
- [x] 约束与索引确认
- [x] 统计口径字段 total_positions 明确为"该棋手走子总步数"
