## header
Created at: 2026-07-09 02:03 EDT
Created by: Codex
Last Modified at: 2026-07-09 02:27 EDT
Last Modified by: Codex

## brief intro
- goal: Requirements for CataChat account integration and the global header notification bug.
- 架构思路: Use the existing CataChess JWT and existing workspace notification storage; avoid another user-facing login or notification system.

## requirements
- The global header bell must show CataChat direct messages, latest broadcast, and workspace notifications in one dropdown.
- Unread badge must include unread workspace notifications using server `read_at`, plus unseen CataChat rows until CataChat has server-side read state.
- Clicking a workspace study/share notification must mark it read and navigate inside CataChess to an existing target route.
- Sharing a study/folder/node with a user must create an in-app notification for that user. Existing ACL updates should also refresh the notification with the current permission.
- Notification creation must be idempotent enough for repeated shares and must not fail the share action if notification insertion conflicts; sharing permissions remain the source of truth.
- Opening CataChat conversations must continue passing the current CataChess JWT to avoid a separate login prompt.

## non-goals
- Do not rebuild a full CataChat UI inside this loop.
- Do not add browser push or email notification delivery.
