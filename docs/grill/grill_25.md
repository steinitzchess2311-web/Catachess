## topic predictor maia catie loop

Created at: 2026-07-08 23:20 EDT
Created by: Codex
Last Modified at: 2026-07-08 23:20 EDT
Last Modified by: Codex

## 问题 1：Predictor 和 Engine 的边界是什么？

推荐答案：Predictor 是“人类走法预测器”，展示 move probability，不展示客观引擎评分。Engine 继续展示 Stockfish/AlphaZero 的 evaluation。

## 问题 2：Maia 用哪条路线？

推荐答案：服务器已有 Maia2 包、脚本和 rapid/blitz 权重，CPU 推理已验证可在约 5 秒返回 top-k。先复用现有本地 Maia2 权重，而不是下载新模型到生产，避免引入不可控依赖。

## 问题 3：Catie 用什么接口？

推荐答案：复用服务器本地 CatieChess `/api/model/probe-position` 队列 API，由 CataChess 后端代理和轮询。不要让前端跨域直接请求 CatieChess。

## 问题 4：如何防止 worker 挤爆服务器？

推荐答案：后端新增 `/api/predictor/predict`，每次请求由统一队列/去重处理。Maia subprocess 受跨进程 slot lock 限制；Catie 由 CatieChess 自己的模型 worker 队列限制，CataChess 侧设置超时和轮询间隔。

## 问题 5：前端怎么设计？

推荐答案：Study 左侧 tab 增加 Predictor；Analysis 页面左侧加横向分栏 Analysis/Predictor。面板只保留 provider、top-k、elo、预测开关和结果表，不保留 Coach/Player/Engine 的旧复杂入口。

## 结果

- 本轮实现两个 provider：Maia 和 Catie。
- Maia 走本地 Maia2 rapid 权重。
- Catie 走 CatieChess 模型队列代理。
- 前端改名为 Predictor，删除旧 Imitator/Coach/Player/Engine 复杂选择。
