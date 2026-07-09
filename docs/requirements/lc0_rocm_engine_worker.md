## header
Created at: 2026-07-08 23:31 EDT
Created by: Codex
Last Modified at: 2026-07-08 23:31 EDT
Lst Modified by: Codex

## brief intro
- goal for this file: Define requirements for replacing the blocked AlphaZero path with LC0/Leela on ROCm GPU.
- 架构思路: Model LC0 as an explicit backend engine provider with bounded concurrency, health reporting, honest unavailable states, and frontend selection support.

## requirements
- AlphaZero runtime/model absence must not block the overall July 8 todo goal.
- Add LC0/Leela as a backend engine capability because the server has ROCm-visible AMD GPU hardware.
- LC0 must have its own binary path, weights path, `onnx-rocm` backend argument, timeout, max nodes, max multipv, and server-wide concurrency limit settings.
- LC0 concurrency must default to 1 process across all gunicorn workers to avoid GPU memory contention.
- `/api/engine/health` must report LC0 availability, binary path, weights path, ROCm probe result, active workers, and concurrency limit.
- Explicit `engine=lc0` must route to LC0.
- Explicit `engine=alphazero` should try LC0 first when configured, then fall back to the existing AlphaZero command worker only if LC0 is unavailable.
- If LC0 is not installed or weights are missing, API responses must be controlled 503 errors, not silent Stockfish fallbacks.
- Frontend engine types must accept `lc0`; UI can keep AlphaZero wording until the production LC0 install is fully verified, but backend source/origin must be specific.
- Tests must cover LC0 capability missing state and basic UCI parsing through a fake process.

## 代办
- Install or build LC0 with ROCm backend on the production server and configure a weights file path.
