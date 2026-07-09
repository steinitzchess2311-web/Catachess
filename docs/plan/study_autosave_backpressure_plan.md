# Study Autosave Backpressure Plan
Created at: 2026-07-08 22:15 EDT
Created by: Codex
Last Modified at: 2026-07-08 22:15 EDT
Last Modified by: Codex

## inferred requirement
- Source requirement: `docs/requirements/study_autosave_backpressure.md`
- Todo source: `patch/docs/Jul_8_代办.md`

## implementation plan
1. Update study autosave documentation so the shorter cadence and backpressure model are explicit.
2. In `patch/studyContext.tsx`, add a 2000 ms autosave constant, latest-state ref, in-flight ref, and queued-save ref.
3. Snapshot tree payload and hash before each request, send it through `api.request` with `X-Tree-Hash`, and coalesce saves while one request is active.
4. In `patch/tree/studyReducer.ts`, allow `MARK_SAVED` to preserve dirty state for stale successful saves.
5. In `patch/backend/study/api.py`, compare canonical content hash plus verified `X-Tree-Hash` metadata and skip duplicate uploads.
6. Run frontend build and Python compile checks.
7. Mark the todo item complete only after local verification, commit, push, and server deployment.

## verification plan
- `python -m py_compile patch/backend/study/api.py backend/modules/workspace/storage/r2_client.py`
- `npm run build`
- Inspect built/source code for `AUTOSAVE_DELAY_MS = 2000`, queued save path, `keepDirty`, and duplicate hash skip.
- Deploy changed files and rebuilt frontend assets to the server, then restart the API service.
