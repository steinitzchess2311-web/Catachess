## header
Created at: 2026-07-08 23:05 EDT
Created by: Codex
Last Modified at: 2026-07-08 23:05 EDT
Lst Modified by: Codex

## brief intro
- goal for this folder: Unit tests for individual engine spot models and HTTP spot wrapper behavior.
- 架构思路: Keep spot-level tests independent from the global engine queue.

## folder structure
|-README.md intro to this folder
|-test_models.py tests spot config/status/metrics data behavior
|-test_spot.py tests single spot client wrapper behavior

## 代办
- Add contract tests if external spot APIs change response format.
