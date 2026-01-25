# Stage 03 - R2 存储方案

目标：确定 PGN 原始文件存储与元数据策略。

## 一、Bucket
- 新建 bucket：catachess-pgn
- 权限：仅后端服务写入/读取

## 二、Key 规范
- PGN 原文：players/{player_id}/{upload_id}/raw.pgn
- 元数据：players/{player_id}/{upload_id}/meta.json

## 三、元数据内容
- checksum
- original_filename
- upload_user_id
- uploaded_at
- parser_version

## 四、重算与版本
- 不覆盖 raw.pgn
- 重算时写新的 upload_id 目录

## Checklist
- [ ] R2 bucket 名称与权限确认
- [ ] Key 规范确认
- [ ] meta.json 内容确认
- [ ] 重算不覆盖规则确认
