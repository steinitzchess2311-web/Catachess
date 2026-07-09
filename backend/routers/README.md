# Backend Routers
Created at: 2026-07-08 21:41 EDT
Created by: Codex
Last Modified at: 2026-07-08 23:05 EDT
Last Modified by: Codex

## brief intro
- goal for this folder: FastAPI routers directly included by `backend/main.py`.
- 架构思路: Keep HTTP request/response schemas at the router boundary and delegate persistence or domain logic to services/repositories.

## folder structure
|-README.md intro to this folder
|-user_profile.py user profile and public profile endpoints
|-chess_engine.py engine analyze/cache/health/queue endpoints

## 代办
- Expand this README with the remaining live router files after the router inventory is documented.
