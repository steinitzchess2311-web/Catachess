## topic lc0 rocm engine worker loop

Created at: 2026-07-08 23:31 EDT
Created by: Codex
Last Modified at: 2026-07-08 23:31 EDT
Last Modified by: Codex

## 问题 1：AlphaZero 原生 worker 不可用时是否阻塞总 goal？

推荐答案：不阻塞。用户明确允许切到 LC0；LC0 是 AlphaZero/Leela 系引擎，适合在 ROCm GPU 上跑，工程上应作为同一个“神经网络引擎能力”继续推进。

## 问题 2：当前服务器 GPU 事实是什么？

推荐答案：Tailscale 活跃服务器是 `100.70.248.39`。`rocminfo` 可用，看到 AMD Radeon 8060S Graphics；`lc0` 当前未安装；Stockfish 已安装在 `/usr/games/stockfish`。

## 问题 3：前端应该如何命名？

推荐答案：短期保留用户已看到的 AlphaZero 入口，但后端 health/detail 明确显示 LC0/Leela ROCm 状态；若 LC0 成功部署，再把选项文案改成 `Leela/LC0` 或 `AlphaZero/LC0`，避免误导。

## 问题 4：并发/显存如何保护？

推荐答案：LC0 默认全机最多 1 个 worker，使用与 Stockfish 相同的跨 gunicorn 文件锁；后续如 GPU 利用率稳定，再配置到 2。请求超时必须受控，未安装二进制/权重时返回 503。

## 问题 5：本轮做到哪里算完成？

推荐答案：先完成 CataChess 后端 LC0 worker 能力、health、engine 路由、前端类型支持和测试；真实 LC0 安装/权重下载若受 apt/ROCm 包源影响，可作为部署步骤继续推进，但不能影响已完成的 Stockfish/Predictor goal。

## 结果

- 采用 LC0 `onnx-rocm` 作为 AlphaZero 阻塞项的替代实现方向。
- 先让产品和 API 明确支持 `engine=lc0`，并把 `alphazero` 映射到 LC0 优先、AlphaZero command fallback。
- 部署时如果缺少 LC0 二进制或权重，health 必须明确 unavailable。
