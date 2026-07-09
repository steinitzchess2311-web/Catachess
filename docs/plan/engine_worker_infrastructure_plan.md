## header
Created at: 2026-07-08 22:50 EDT
Created by: Codex
Last Modified at: 2026-07-08 23:25 EDT
Lst Modified by: Codex

## brief intro
- goal for this file: Execution plan inferred from `docs/requirements/engine_worker_infrastructure.md`.
- 架构思路: Build the smallest production path first: backend local Stockfish runner, engine registry/health, then frontend selector and deployment checks.

## plan
1. Add backend engine configuration for local Stockfish binary, Stockfish worker limit, AlphaZero command/model/device, and queue default of 10 workers.
2. Add a local Stockfish UCI runner that starts one short-lived process per request, sends UCI commands, parses best depth MultiPV lines, and is protected by a cross-process slot limiter so gunicorn workers share one global cap.
3. Add an AlphaZero worker shell with independent cross-process slot limiter and strict unavailable errors when runtime/model/GPU is missing.
4. Route `engine=stockfish` and `engine=alphazero` through the new server workers; keep `engine=auto` compatible with cloud/Stockfish fallback.
5. Expand `/api/engine/health` and queue stats metadata for product monitoring.
6. Update frontend engine client/types/hook/settings so explicit engine selection calls the server and the UI labels are clear.
7. Update design docs and folder READMEs touched by this change.
8. Verify with backend unit tests, py_compile, frontend build, remote deploy smoke checks.

## 代办
- Load-test `/api/engine/analyze` after production traffic patterns are known.
