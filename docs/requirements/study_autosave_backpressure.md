# Study Autosave Backpressure Requirements
Created at: 2026-07-08 22:15 EDT
Created by: Codex
Last Modified at: 2026-07-08 22:15 EDT
Last Modified by: Codex

## brief intro
- goal for this requirement: Make patch study autosave safe under a shorter 2 second cadence and reduce unnecessary backend/R2 load.
- 架构思路: Treat autosave as a coalesced durability pipeline. The client prevents request pileups, and the server skips duplicate content writes.

## requirements
- Autosave delay must be 2 seconds after the tree becomes dirty.
- A single study editor tab must not send overlapping tree save requests for the same provider state.
- Edits made while a save request is in flight must trigger a follow-up save after the active request completes.
- A successful stale save must not clear the dirty flag for newer unsaved edits.
- Failed saves must keep dirty state so manual save or the next autosave can retry.
- The client must continue sending a SHA-256 tree hash in `X-Tree-Hash`.
- The server must skip an R2 upload when existing object metadata proves the submitted tree content is unchanged, using canonical `content-hash` and verified `X-Tree-Hash` metadata.
- The tree JSON schema must remain unchanged.
- This change must not claim full multi-user realtime conflict resolution; that belongs to the later study permission/collaboration project.

## acceptance
- Code shows a 2000 ms autosave delay.
- Code coalesces in-flight saves and queues a retry when needed.
- Code preserves dirty state when a save response corresponds to an older tree snapshot.
- Backend returns success without rewriting R2 when metadata proves the tree content is unchanged.
- Frontend build and Python compile checks pass.
