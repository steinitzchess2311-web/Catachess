## header
Created at: 2026-07-09 02:03 EDT
Created by: Codex
Last Modified at: 2026-07-09 02:27 EDT
Last Modified by: Codex

## brief intro
- goal: Plan the CataChat/header notification implementation loop.
- 架构思路: Backend first for reliable study share notifications, then header aggregation and verification.

## plan
- Read CataChat, workspace share, and workspace notification endpoints.
- Add workspace share notification creation to `ShareService.share_with_user`.
- Add focused backend tests for share notification creation and list/read endpoint behavior if existing fixtures support it.
- Update header types and state to merge CataChat broadcasts/messages with workspace notifications.
- Use the workspace notification read API for workspace notification clicks and route internally for study/workspace targets.
- Build frontend and run targeted backend tests.
- Commit, push, deploy, and smoke test `/api/v1/workspace/notifications` plus `/api/catchat/notifications`.

## implementation notes
- Study invite links use `/patch/workspace/:id` because the router does not define `/study/:id`.
- Header workspace notification read state uses the existing `/api/v1/workspace/notifications/read` endpoint; CataChat messages retain the current local seen cache until CataChat exposes server read state.
