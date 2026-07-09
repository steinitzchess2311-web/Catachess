## topic engine worker deployment loop

Created at: 2026-07-08 22:50 EDT
Created by: Codex
Last Modified at: 2026-07-08 23:25 EDT
Last Modified by: Codex

## 问题 1：这轮要一次性完成什么闭环？

推荐答案：先完成“可部署、可监控、不会挤爆服务器”的服务端引擎闭环，并把前端选择器接上。Stockfish 必须走服务器本机 worker；AlphaZero 必须作为产品级 engine option 暴露健康状态，但在当前服务器 GPU 驱动不可用时不能伪装成可用。

## 问题 2：为什么不继续只调用 sf.catachess.com？

推荐答案：用户明确要求“服务器上部署 stockfish worker 和 alphazero worker”，当前 `engine='sf'` 实际是 HTTP upstream。服务器已有 `/usr/games/stockfish`，所以必须把本机 Stockfish worker 作为第一生产路径。

## 问题 3：并发限制怎么做？

推荐答案：保留现有 API 队列/去重，但把 worker 并发默认升到 10，并在本机 Stockfish runner 内加跨进程 10 路 slot limiter 作为硬限制。AlphaZero 使用独立跨进程 1 路 slot limiter，避免未来 GPU worker 抢占整个服务器。

## 问题 4：AlphaZero 当前怎么处理才工程上诚实？

推荐答案：服务器 `nvidia-smi` 当前无法连接 NVIDIA driver，因此这一圈不能声称 AlphaZero 推理已真正可用。应注册 AlphaZero worker、配置模型/命令入口、健康检查和受控错误；待 GPU 驱动/模型路径可用后只需补命令。

## 问题 5：前端怎么避免混乱？

推荐答案：只提供清晰的 Engine selector：Auto、Stockfish、AlphaZero。Auto 保持现有 WASM 优先、服务端 fallback；Stockfish 直接请求服务端本机 worker；AlphaZero 若不可用，显示明确错误，不展示旧 Stockfish 结果冒充。

## 问题 6：如何验证？

推荐答案：后端单测覆盖 Stockfish UCI parser、队列限流配置、AlphaZero 不可用错误；本地 py_compile；前端 build；服务器部署后 curl `/api/engine/health`、`/api/engine/queue/stats` 和一条 Stockfish 分析请求。

## 结果

- 本轮先实施 Stockfish 本机 worker、AlphaZero worker 注册/健康/受控不可用、前端 engine selector 和 engine 面板清理。
- 不在 GPU 不可用的服务器上伪造 AlphaZero 分析结果。
