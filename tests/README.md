## header
Created at: 2026-07-08 23:23 EDT
Created by: Codex
Last Modified at: 2026-07-08 23:23 EDT
Lst Modified by: Codex

## brief intro
- goal for this folder: Root test suite for backend, chess rules, engine orchestration, predictor routing, workspace, tagger, signup/auth, and patch integration.
- 架构思路: Keep targeted behavior tests close to the public routers and service adapters they protect.

## folder structure
|-test_predictor_router.py Maia/Catie predictor adapter behavior tests.
|-chess_engine/ Local engine worker tests.
|-modules/ Module-level API and service tests.

## 代办
The local `.venv` in this checkout is not portable, so tests require a healthy Python environment with `requirements.txt` installed.
