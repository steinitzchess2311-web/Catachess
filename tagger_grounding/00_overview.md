# Stage 00 - 总览与执行规则

目标：给出可落地执行的端到端计划。员工只看本目录即可完成交付。

## 一、必须遵守的执行规则
1) 每个 Stage 完成后，必须在 `tagger_grounding/summary/` 写 `stageXX_summary.md`。
2) 每个新建代码文件不得超过 200 行；超过则必须拆分到新文件夹中（语义拆分）。
3) 每次完成任务，必须逐条对照本 Stage 的 checklist，核对后打勾。
4) 未完成 checklist 不允许进入下一个 Stage。

## 二、交付范围
- 后端：tagger pipeline（PGN 解析、模糊匹配、去重、统计、存储、导出）
- 前端：Players 页面 + 上传 + 统计展示 + 导出
- 存储：R2 + Postgres

## 三、总流程图（文本版）
1) 新建棋手档案
2) 上传 PGN → R2 存档
3) 解析 PGN → 模糊匹配 → 确认
4) 逐步走子 → tagger 分析
5) 统计累加（白/黑/总）
6) 写入 Postgres → UI 展示

## 四、阶段清单
- Stage 01：需求冻结与规范定义
- Stage 02：架构设计与接口规范
- Stage 03：R2 存储与元数据
- Stage 04：Postgres 表结构与索引
- Stage 05：后端 API + 服务层
- Stage 06：Pipeline 实现（PGN → tag）
- Stage 07：去重与名称匹配策略
- Stage 08：引擎调用与重试策略
- Stage 09：前端 Players 页面与路由
- Stage 10：导出与报表
- Stage 11：运维与监控
- Stage 12：测试与验收
- Stage 13：上线准备

## Checklist
- [ ] 已理解规则：每个 Stage 完成后写 summary
- [ ] 已理解规则：新建代码文件不超过 200 行
- [ ] 已理解规则：完成 checklist 才能进入下一阶段
