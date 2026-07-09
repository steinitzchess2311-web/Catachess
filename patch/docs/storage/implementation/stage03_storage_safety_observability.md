# Stage 03 - Safety + Observability
Created at: 2026-07-08 22:15 EDT
Created by: Codex
Last Modified at: 2026-07-08 22:15 EDT
Last Modified by: Codex

## Goal
- Add lightweight concurrency guard and logging for saves.
- Keep save observability meaningful after autosave is reduced to 2 seconds.

## Must-reference paths
- patch/studyContext.tsx
- patch/backend/study/api.py
- patch/docs/storage/overview_plan.md

## Constraints
- Keep tree.json schema unchanged (no new required fields).

## Checklist
- [ ] Add optional client-side hash/etag to avoid accidental overwrite (best-effort).
- [ ] Log save attempts and outcomes (frontend console or backend logger).
- [ ] Ensure retry after failure keeps dirty flag.
- [ ] Coalesce overlapping autosaves and queue a follow-up save when edits happen during an in-flight request.
- [ ] Skip duplicate server-side R2 uploads when existing content metadata matches the client hash.
- [ ] Document any trade-offs in summary.
- [ ] Write completion report in patch/docs/storage/summary/Storage_stage03.md.
