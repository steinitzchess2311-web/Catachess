# Stage 3C - 性能与容量评估（产品级门槛）

## 约束（必须写在每个 stage 文档开头）
- [ ] 每完成一项任务，必须勾选对应 checkbox。
- [ ] 如果遇到阻塞或不确定，必须直接写明问题，不允许猜测后勾选。
- [ ] 禁止“先勾选后补做”。
- [ ] 禁止谎报进度；我会抽查对比代码。

---

## 本 Stage 目标（产品级）
确保 PGN v2 在真实负载下可用，避免导入/渲染/分析导致系统卡死。

---

## 分计划（Checklist）

### A. 导入性能
- [x] 使用大 PGN（>10MB, >500 章）导入测试
  - 数据集：`docs/performance_reports/large_pgn_generated.pgn`
  - 记录：`docs/performance_reports/stage3c_performance_report.md`
- [x] 记录耗时与内存
  - 记录：`docs/performance_reports/import_perf.log`
- [ ] 若超阈值：调整拆分/异步处理
  - 阻塞：导入测试超时（>300s），尚未进入优化/拆分改造。

### B. 渲染性能
- [ ] 前端渲染复杂变例（5+ 层）
  - 阻塞：需要浏览器 Performance panel 实测，尚未执行。
- [ ] 确认 UI 不冻结（滚动/点击流畅）
  - 阻塞：未完成渲染性能实测。
- [ ] 必要时做虚拟渲染或分段加载
  - 阻塞：依赖前端性能实测结果。

### C. Tagger/Engine 负载
- [ ] 使用 fen_index 做批量 tagger 分析
  - 阻塞：仅完成 mainline 1 节点测试（见 `docs/performance_reports/tagger_perf.log`）。
- [ ] 记录 CPU/内存
  - 记录：`docs/performance_reports/tagger_perf.log`（positions=1）。
- [ ] 必要时加入限流/队列
  - 阻塞：需先完成批量负载测试再评估。

### D. 性能门槛
- [ ] 导入单章 PGN < 2s（目标）
  - 阻塞：当前导入测试超时（见 `docs/performance_reports/stage3c_performance_report.md`）。
- [ ] 前端渲染 < 300ms（目标）
  - 阻塞：渲染性能未实测。
- [ ] Tagger 每 100 节点 < 5s（目标）
  - 阻塞：仅 1 节点测试，未达批量门槛。

---

## 输出物（本阶段交付）
- 性能测试报告
- 性能优化清单
- 明确上线门槛
