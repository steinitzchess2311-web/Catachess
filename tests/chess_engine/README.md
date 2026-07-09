## header
Created at: 2026-07-08 23:05 EDT
Created by: Codex
Last Modified at: 2026-07-08 23:31 EDT
Lst Modified by: Codex

## brief intro
- goal for this folder: Tests for chess engine clients, local workers, multi-spot routing, and engine models.
- 架构思路: Prefer deterministic unit tests over live network engine calls; keep live external checks gated elsewhere.

## folder structure
|-README.md intro to this folder
|-test_local_workers.py tests local Stockfish parsing/capability plus LC0 and AlphaZero unavailable semantics
|-orchestrator/ tests multi-spot engine routing and failover
|-spot/ tests individual engine spot models and wrappers

## 代办
- Add an opt-in integration test that invokes `/usr/games/stockfish` on systems where it is installed.
