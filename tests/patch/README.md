# Patch Tests
Created at: 2026-07-08 22:15 EDT
Created by: Codex
Last Modified at: 2026-07-08 22:15 EDT
Last Modified by: Codex

## brief intro
- goal for this folder: Integration and focused behavior tests for patch study import, edit, export, replay, and tree save flows.
- 架构思路: Keep tests near the patch domain while exercising public backend/API helper behavior instead of private implementation details.

## folder structure
|-README.md intro to this folder
|-test_stage12_integration.py patch study import/edit/writeback and autosave backend dedupe tests

## 代办
- Add browser-level autosave tests when the frontend test runner is stable.
