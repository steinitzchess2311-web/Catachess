## header
Created at: 2026-07-09 00:52 EDT
Created by: Codex
Last Modified at: 2026-07-09 00:52 EDT
Lst Modified by: Codex

## brief intro
- goal for this folder: Centralize workspace authorization, inheritance, discussion, and limit policies.
- 架构思路: Policies answer capability questions and raise clear domain errors for endpoint translation.

## folder structure
|-permissions.py shared node permission helpers.
|-permissions_core.py core permission matrix.
|-discussion_permissions.py discussion-specific access guards.
|-limits.py workspace and study size limits.

## 代办
- Keep new write-boundary checks here instead of duplicating ACL logic in endpoints.
