# Patch
Created at: 2026-07-08 21:41 EDT
Created by: Codex
Last Modified at: 2026-07-08 21:41 EDT
Last Modified by: Codex

## brief intro
- goal for this folder: Production-reachable replacement and extended modules imported by the active `frontend/web` app through the `@patch` alias.
- 架构思路: Keep patch-owned study, workspace, engine, game, and feature modules colocated while they remain wired into the frontend app.

## folder structure
|-README.md intro to this folder
|-docs/ patch implementation notes and todo documents
|-modules/ feature modules used through the `@patch` alias
|-engine/ browser and remote engine integration code
|-board/ patch study board code
|-sidebar/ patch study sidebar code
|-tree/ patch study move tree code
|-chessJS/ chess rules helpers

## 代办
- Continue documenting production-reachable patch modules as they are modified.
