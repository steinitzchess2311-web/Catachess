## header
Created at: 2026-07-09 01:10 EDT
Created by: Codex
Last Modified at: 2026-07-09 01:10 EDT
Lst Modified by: Codex

## brief intro
- goal for this folder: Configure the synchronous SQLAlchemy database engine and session factory used by legacy backend routes.
- 架构思路: Keep engine construction isolated so production Postgres pooling and local SQLite tests can use appropriate SQLAlchemy options.

## folder structure
|-db_engine.py creates the sync SQLAlchemy engine from application settings.
|-session.py exposes the sync session factory.
|-deps.py FastAPI dependency for sync DB sessions.

## 代办
- Prefer async workspace database dependencies for workspace modules; keep sync DB usage limited to legacy account routes.
