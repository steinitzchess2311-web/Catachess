## header
Created at: 2026-07-09 00:52 EDT
Created by: Codex
Last Modified at: 2026-07-09 00:52 EDT
Lst Modified by: Codex

## brief intro
- goal for this folder: Define Pydantic request and response contracts for workspace APIs.
- 架构思路: Schemas are stable wire contracts and may include computed capability fields needed by the frontend.

## folder structure
|-node.py node create/update/list/response schemas.
|-study.py study, chapter, import, and PGN response schemas.
|-share.py share and ACL response schemas.
|-variation.py legacy variation mutation schemas.

## 代办
- Preserve backward-compatible optional fields when exposing new capabilities.
