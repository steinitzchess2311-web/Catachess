## header
Created at: 2026-07-09 02:03 EDT
Created by: Codex
Last Modified at: 2026-07-09 02:27 EDT
Last Modified by: Codex

## brief intro
- goal: Grill the CataChat account integration and header notification loop before implementation.
- 架构思路: Keep CataChess as the authenticated shell; the header bell should aggregate chat, broadcasts, and workspace share/study invites without requiring users to discover a separate notification surface.

## grill
- Why separate CataChat remains painful: the user sees message previews in CataChess, but opening the bell punts to another domain. We should at least make the bell useful in CataChess and pass the existing JWT when opening a chat route.
- Study invitation semantics are currently just ACL shares. That is acceptable if the notification body says the actor invited/shared a study and the click target opens the study.
- Avoid a new notification store. Workspace already has notification tables and API; share_service publishes ACL events but does not reliably create a share invite notification in production, so write it directly in the share transaction.
- Header seen state should not be localStorage-only for workspace notifications. Use `read_at` and mark workspace notifications read through the existing API.
- The app has no `/study/:id` route; study invite notifications must target an existing study route such as `/patch/workspace/:id`.

## decision
- Add direct in-app notification creation in `ShareService.share_with_user`.
- Extend header to fetch `/api/v1/workspace/notifications` and merge those rows with CataChat messages/broadcasts.
- Keep CataChat external route opening as a bridge for chat conversations while the CataChess header owns previews and unread count.
