# Patch Tree
Created at: 2026-07-08 21:41 EDT
Created by: Codex
Last Modified at: 2026-07-08 22:15 EDT
Last Modified by: Codex

## brief intro
- goal for this folder: Frontend study tree data structure, cursor logic, reducer state, and type definitions for patch study chapters.
- 架构思路: Keep pure tree operations and reducer state independent from React so the in-browser representation persisted to backend `tree.json` endpoints can be reasoned about separately.

## folder structure
|-README.md intro to this folder
|-StudyTree.ts move tree mutation and traversal helpers
|-studyReducer.ts pure reducer for study state, dirty state, save metadata, and train mode
|-type.ts persisted tree JSON TypeScript types and upgrade helpers

## 代办
- Add reducer-level tests for autosave dirty-state edge cases.
