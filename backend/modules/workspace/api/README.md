## header
Created at: 2026-07-09 00:52 EDT
Created by: Codex
Last Modified at: 2026-07-09 00:52 EDT
Lst Modified by: Codex

## brief intro
- goal for this folder: Expose workspace FastAPI routers, schemas, dependencies, and websocket entry points.
- 架构思路: Endpoint modules stay thin, schemas define wire contracts, and shared dependencies connect services/repositories.

## folder structure
|-router.py root workspace API router.
|-deps.py authenticated API dependencies.
|-schemas/ request and response models.
|-endpoints/ HTTP route modules.
|-websocket/ websocket route modules.

## 代办
- Keep authorization checks centralized through dependencies or domain helpers when possible.
