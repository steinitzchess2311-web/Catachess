## header
Created at: 2026-07-08 22:50 EDT
Created by: Codex
Last Modified at: 2026-07-08 23:25 EDT
Lst Modified by: Codex

## brief intro
- goal for this file: Define production requirements for server-side engine workers and the engine selector UI.
- 架构思路: Treat each engine as an explicit backend capability with queueing, concurrency limits, health reporting, and honest unavailable states.

## requirements
- Server Stockfish analysis must run through the deployed server instead of relying only on an external HTTP upstream.
- Stockfish concurrency must be bounded to at most 10 simultaneous analyses across the whole deployed server, including all gunicorn worker processes.
- Engine requests must stay queued and deduplicated so many users do not spawn unlimited engine processes.
- AlphaZero must be represented as a separate worker capability with its own server-wide limit and health state.
- If AlphaZero GPU/model/runtime is unavailable, the API must return a controlled unavailable error and health metadata rather than silently falling back to another engine.
- `/api/engine/health` must report configured engines, queue status, and availability.
- The frontend engine controls must let users choose Auto, Stockfish, or AlphaZero.
- Auto may keep browser Stockfish WASM first, but explicit Stockfish/AlphaZero selections must call the server with that engine choice.
- The engine panel must remain plain and product-grade: compact controls, clear score, no decorative status chips.
- Existing cache behavior must remain engine-specific so AlphaZero/Stockfish results are not mixed.

## 代办
- Add a true AlphaZero command/model once a GPU driver and model artifact are installed on the server.
