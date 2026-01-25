# Stage 10 - 导出与报表

目标：导出白/黑/总三套统计。

## 一、导出格式
- JSON：包含 metadata + tag_counts + percentages + denominators\n  - denominators = white_moves / black_moves / total_moves\n  - metadata 包含 engine_version / depth / multipv / stats_version\n- CSV：每行 tag，列 = count_white/pct_white/white_moves/count_black/pct_black/black_moves/count_total/pct_total/total_moves

## 二、编码与排序
- UTF-8
- 默认按总计百分比降序

## 三、统计范围标识\n- 输出必须包含 upload_ids 或时间范围（from/to）。\n- 便于解释“统计覆盖哪些上传”。

## Checklist
- [ ] JSON 字段固定
- [ ] CSV 列顺序固定
- [ ] 排序规则固定
