# Backend
Created at: 2026-07-08 22:04 EDT
Created by: Codex
Last Modified at: 2026-07-08 22:04 EDT
Last Modified by: Codex

## brief intro
- goal for this folder: Production FastAPI backend deployed through `backend.main:app`.
- 架构思路: Keep HTTP routers thin, shared infrastructure in `core`, feature modules in `modules`, SQLAlchemy models in `models`, and reusable business operations in `services`.

## folder structure
|-README.md intro to this folder
|-main.py FastAPI app wiring, startup hooks, CORS, routers, and production initialization
|-routers/ top-level HTTP routers included by `main.py`
|-modules/ larger feature modules such as workspace, blogs, and tagger
|-core/ shared chess, engine, security, DB, logging, PGN, and tagger internals
|-models/ sync SQLAlchemy models for auth/game/profile data
|-schemas/ shared Pydantic schemas
|-services/ reusable service functions for older sync APIs

## 代办
- Continue splitting legacy sync APIs and newer workspace async APIs into clearer bounded modules.
