# Stage 07 - 去重与名称匹配

目标：避免重复计数并解决输入名误差。

## 一、去重策略
- game_hash = 规范化 headers + 主线走子
- headers 规范化规则：仅 White/Black/Date/Event/Result（以本规则为唯一标准）
- 主线走子统一为 UCI（推荐）
- 存储唯一键：player_id + game_hash

## 二、匹配策略
- 规范化：去标点/空格/大小写/重音
- 优先级：aliases > display_name > 模糊匹配 White/Black
- 模糊匹配：编辑距离或相似度阈值
- 多候选：人工确认

## Checklist
- [ ] game_hash 规范化规则固定
- [ ] 去重唯一键固定
- [ ] 模糊匹配优先级固定
- [ ] 人工确认流程固定
