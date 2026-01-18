# Stage 4 - 产品级可用性保障（检索/一致性/可追溯）

## 约束（必须写在每个 stage 文档开头）
- [ ] 每完成一项任务，必须勾选对应 checkbox。
- [ ] 如果遇到阻塞或不确定，必须直接写明问题，不允许猜测后勾选。
- [ ] 禁止“先勾选后补做”。
- [ ] 禁止谎报进度；我会抽查对比代码。

---

## 本 Stage 目标（产品级）
让“目录树在 Postgres、棋谱在 R2”的双存储结构对用户透明：
- 用户/前端不需要知道 R2 key 如何拼接
- 后端提供稳定、可检索、可追溯的 API
- 数据一致性可校验、可修复
- 任何异常可追踪与可解释

---

## 分计划（Checklist）

### A. 用户可用的检索链路（产品级要求）
- [ ] 对外 API 必须提供“从 study 到 PGN”的完整可用链路：
  - [ ] `GET /studies/{study_id}` 返回 chapter 列表
  - [ ] 每个 chapter 返回：`chapter_id`, `title`, `pgn_status`, `pgn_hash`, `pgn_size`, `last_synced_at`
  - [ ] `GET /studies/{study_id}/chapters/{chapter_id}/pgn` 由后端读取 R2
- [ ] 前端禁止拼接 R2 key；只能调用 API

### B. 数据一致性规则（强约束）
- [ ] `chapters.r2_key` 必须与 `R2Keys.chapter_pgn(chapter_id)` 对齐
- [ ] 在写入/同步时执行一致性校验：
  - [ ] 不一致即记录告警
  - [ ] 迁移阶段允许自动回填修复
- [ ] `pgn_hash` 与 `pgn_size` 必须更新（用于一致性与审计）

### C. 缺失数据的可见性与恢复
- [ ] 当 `chapter` 存在但 R2 不存在 PGN 时：
  - [ ] API 返回明确 `pgn_status = missing`
  - [ ] 前端显示可重建/重试按钮
- [ ] 提供“重建 PGN”内部接口（管理员/运维）：
  - [ ] 从 DB Variation 重建 NodeTree
  - [ ] 重新生成 PGN 写回 R2

### D. 迁移阶段的校验任务（一次性/可复用）
- [ ] 新增“对齐扫描任务”（手动触发脚本或管理命令）：
  - [ ] 遍历所有 study -> chapters
  - [ ] 校验 r2_key 是否为标准 key
  - [ ] 校验 PGN 是否存在
  - [ ] 校验 hash/size 与 R2 一致
- [ ] 输出报告（JSON/CSV）：
  - [ ] 总数 / 不一致数 / 修复数 / 失败数

### E. 监控与告警（产品稳定性）
- [ ] 新增日志维度：`study_id`, `chapter_id`, `r2_key`
- [ ] 对以下异常打点：
  - [ ] R2 404（PGN 丢失）
  - [ ] r2_key 不一致
  - [ ] hash/size 不一致
- [ ] 定义最低告警门槛（例如每小时 > N 次 404）

### F. 对外文档与客服支持
- [ ] 写清楚“PGN 存储与检索规则”对外说明
- [ ] 在运维文档中新增：
  - [ ] 如何重建 PGN
  - [ ] 如何修复 r2_key
  - [ ] 如何排查 PGN 不存在问题

---

## 输出物（本阶段交付）
- 产品级 API 检索链路
- 数据一致性校验机制
- 批量扫描/修复脚本（或管理命令）
- 监控与告警指标
- 运维/对外说明文档

