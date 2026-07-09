# Storage System Plan (Patch)
Created at: 2026-07-08 22:15 EDT
Created by: Codex
Last Modified at: 2026-07-08 22:15 EDT
Last Modified by: Codex

## Goal
- Add manual Save + auto-save for Study tree.json stored in R2.
- Only save when there are changes, with debounce/idle protection.
- Keep autosave safe when the debounce is shortened to 2 seconds by coalescing in-flight writes.

## Scope
- Frontend: Patch Study UI + StudyContext.
- Backend: existing tree.json PUT endpoint (no new storage format).

## Constraints
- tree.json is the only persisted structure.
- No FEN in tree.json.
- Save uses existing PUT /study-patch/chapter/{chapter_id}/tree.
- This storage layer does not provide full multi-user conflict resolution; realtime collaboration is a separate study permission project.

## Milestones
- Stage 01: Frontend state + Save entrypoint (manual + auto-save).
- Stage 02: Save feedback + error handling + UX indicators.
- Stage 03: Optional concurrency guard (hash/updatedAt) and observability.
- Stage 04: Autosave backpressure, 2 second debounce, and duplicate R2 write skipping.

## Success Criteria
- Manual Save writes to R2 and clears dirty flag.
- Auto-save triggers only when isDirty=true and after debounce/idle.
- Failures surface as SAVE_ERROR and do not clear dirty flag.
- Autosave never runs overlapping requests from one editor tab.
- A save response for an old tree snapshot cannot clear the dirty flag for newer edits.
- Server skips R2 writes when metadata proves unchanged content through canonical content hash or verified client tree hash.
