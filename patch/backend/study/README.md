# Patch Study Backend
Created at: 2026-07-08 21:41 EDT
Created by: Codex
Last Modified at: 2026-07-08 22:15 EDT
Last Modified by: Codex

## brief intro
- goal for this folder: Study tree DTOs, conversion, API helpers, and migration helpers for the patch study page.
- 架构思路: The workspace studies router imports these helpers to read and write `tree.json` chapter state while keeping patch-specific conversion logic isolated.

## folder structure
|-README.md intro to this folder
|-api.py FastAPI router helpers for patch study tree read, write, and PGN export
|-models.py Pydantic DTOs for patch study tree API payloads
|-conversion.py conversion helpers between PGN-like data and patch study tree structures
|-migration.py migration helper for moving legacy study data into tree JSON storage

## 代办
- Add explicit tests around save dedupe and future collaboration conflict semantics.
