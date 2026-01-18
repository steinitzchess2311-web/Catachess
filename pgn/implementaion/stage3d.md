# Stage 3D - Legacy 退役与对外说明

## 约束（必须写在每个 stage 文档开头）
- [ ] 每完成一项任务，必须勾选对应 checkbox。
- [ ] 如果遇到阻塞或不确定，必须直接写明问题，不允许猜测后勾选。
- [ ] 禁止“先勾选后补做”。
- [ ] 禁止谎报进度；我会抽查对比代码。

---

## 本 Stage 目标（产品级）
完成 legacy 功能退役，确保文档与外部行为一致。

---

## 分计划（Checklist）

### A. Legacy 退役清单（必须明确）
- [ ] `backend/modules/workspace/pgn/serializer/*` 标记为 deprecated
- [ ] `backend/core/chess_basic/pgn/*` 仅用于对弈记录（不再用于 study）
- [ ] 旧 API 文档标注 deprecated

### B. 接口对外说明
- [ ] 新增或更新文档：
  - [ ] `/show` 与 `/fen` 为标准接口
  - [ ] `/moves/mainline` 进入退役期
- [ ] 前端默认启用 ShowDTO（灰度结束后）

### C. 清理与锁定
- [ ] 禁止新代码再依赖旧 serializer
- [ ] 设定删除时点（版本号或日期）

---

## 输出物（本阶段交付）
- Legacy 退役清单
- 对外接口文档更新
- 退役时间表

