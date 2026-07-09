# Patch Backend
Created at: 2026-07-08 21:41 EDT
Created by: Codex
Last Modified at: 2026-07-08 22:15 EDT
Last Modified by: Codex

## brief intro
- goal for this folder: Backend helpers used by production-reachable patch study endpoints.
- 架构思路: Keep patch-specific API helpers and DTO conversion close to the frontend patch study implementation while the live workspace router imports them.

## folder structure
|-README.md intro to this folder
|-study/ patch study tree API helpers, DTOs, migration utilities, and PGN conversion

## 代办
- Keep this folder documented because it is part of the backend runtime surface.
