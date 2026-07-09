## header
Created at: 2026-07-08 23:05 EDT
Created by: Codex
Last Modified at: 2026-07-08 23:05 EDT
Lst Modified by: Codex

## brief intro
- goal for this folder: Unit tests for multi-spot engine orchestration.
- 架构思路: Mock spot clients so routing, retry, and failover behavior can be tested without external engine services.

## folder structure
|-README.md intro to this folder
|-test_orchestrator.py tests retry/failover behavior
|-test_pool.py tests spot pool registration and selection
|-test_selector.py tests spot ranking rules

## 代办
- Add stress tests for mixed healthy/degraded spot pools if multi-spot mode is re-enabled.
