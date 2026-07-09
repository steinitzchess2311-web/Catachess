## header
Created at: 2026-07-08 23:31 EDT
Created by: Codex
Last Modified at: 2026-07-08 23:31 EDT
Lst Modified by: Codex

## brief intro
- goal for this file: Execution plan inferred from `docs/requirements/lc0_rocm_engine_worker.md`.
- 架构思路: Extend the already deployed local worker registry instead of adding a parallel engine stack.

## plan
1. Add LC0 settings in `backend/core/config.py`.
2. Extend local engine workers with an `Lc0Worker` that runs UCI, parses LC0 `info` lines through the existing Stockfish parser, and uses `CrossProcessSlotLimiter`.
3. Add ROCm/LC0 capability probing with controlled missing-state detail.
4. Route `engine=lc0` and `engine=alphazero` through LC0 first, with the existing AlphaZero command worker as fallback.
5. Expand frontend engine types to understand `lc0` and keep labels clear.
6. Add targeted tests for missing LC0 and fake LC0 UCI output.
7. Verify local tests, py_compile, frontend build, remote deploy, and production health.

## 代办
- If package installation is required, document the exact production install command and model artifact path after probing server package availability.
