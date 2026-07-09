# Study Autosave Backpressure Grill
Created at: 2026-07-08 22:15 EDT
Created by: Codex
Last Modified at: 2026-07-08 22:15 EDT
Last Modified by: Codex

## topic study autosave 2 second durability and request backpressure

## Q1. What can break if the autosave delay is reduced from 5 seconds to 2 seconds?
- A shorter debounce increases request frequency. If the client starts a new save while a previous save is still in flight, edits made during the older request can be marked saved incorrectly when the older request returns.
- Recommended answer: keep the 2 second debounce, but enforce one in-flight save per StudyProvider and queue exactly one follow-up save when edits happen during the active request.

## Q2. Does the current code already prevent duplicate requests?
- It returns early when `state.isSaving` is true, but that simply drops the attempted save. It does not remember that another save is needed after the active request completes.
- Recommended answer: replace the drop behavior with a coalescing queue so high-frequency edits collapse into one follow-up request.

## Q3. Should the server reject stale writes?
- This todo asks whether many simultaneous requests will crash and asks for a safer 2 second autosave cadence. Full optimistic concurrency would affect multi-user editing semantics and belongs with the later viewer/modifier + real-time collaboration work.
- Recommended answer: do not change the tree schema or introduce hard conflict errors here. Add duplicate-content skipping via the existing tree hash metadata, and leave strict collaborative conflict resolution for the upcoming study permission/collaboration change.

## Q4. How should the client know a save actually corresponds to the latest tree?
- A save should snapshot the chapter id, tree payload, and SHA-256 hash before sending. On success, compare the hash of the latest tree with the hash that was sent. Only clear dirty state when they match.
- Recommended answer: extend `MARK_SAVED` with `keepDirty` so successful stale saves can update last saved metadata without losing the unsaved marker.

## Q5. What server-side optimization is available without changing data format?
- The R2 client already writes `content-hash` metadata for JSON uploads. The study API receives `X-Tree-Hash` from the client.
- Recommended answer: when metadata proves unchanged content through canonical `content-hash` or verified `X-Tree-Hash`, return success without a new R2 `put_object`.

## Q6. What should be verified?
- Frontend build must compile with the new save flow.
- Backend Python modules touched must compile.
- The code must visibly contain the 2 second debounce, queued save path, stale-save dirty preservation, and duplicate-hash server skip.
