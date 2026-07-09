## header
Created at: 2026-07-09 00:52 EDT
Created by: Codex
Last Modified at: 2026-07-09 00:52 EDT
Lst Modified by: Codex

## brief intro
- goal for this folder: Provide repository classes for workspace persistence operations.
- 架构思路: Endpoints and services call repositories instead of embedding SQL in UI-facing logic.

## folder structure
|-acl_repo.py ACL and share-link queries.
|-node_repo.py workspace node tree queries.
|-study_repo.py study and chapter metadata queries.
|-variation_repo.py legacy variation tree queries.
|-event_repo.py event history queries.

## 代办
- Keep permission decisions in domain policies/services; repositories should stay persistence-focused.
