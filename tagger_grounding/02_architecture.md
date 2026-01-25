# Stage 02 - 架构设计与接口规范

目标：明确模块分层与 API 边界。

## 一、分层原则
- backend/core：保留单步 tagger 能力
- backend/modules/tagger：pipeline 与存储调度
- patch/modules/tagger：前端 UI 与 API 调用

## 二、API 草案
- POST /api/tagger/players
- GET /api/tagger/players
- GET /api/tagger/players/:id
- POST /api/tagger/players/:id/uploads
- GET /api/tagger/players/:id/stats
- GET /api/tagger/players/:id/exports?format=csv|json

## 三、状态模型
- pgn_uploads.status：pending / processing / needs_confirmation / done / failed / completed_with_errors

## 四、文件结构约束
- 新建代码文件不得超过 200 行
- 超过必须拆分到新文件夹，按语义拆分

## Checklist
- [ ] 确认后端分层不侵入 core
- [ ] API 列表已冻结
- [ ] 状态模型已冻结
- [ ] 代码文件 200 行限制已写入规则
