# Frontend Jank Reduction Plan
Created at: 2026-07-08 22:36 EDT
Created by: Codex
Last Modified at: 2026-07-08 22:36 EDT
Last Modified by: Codex

## inferred requirement
- Source requirement: `docs/requirements/frontend_jank_reduction.md`
- Todo source: `patch/docs/Jul_8_代办.md`

## implementation plan
1. Document the diagnosis and bounded requirements before code changes.
2. Update `frontend/web/src/components/header/Header.tsx` so active-game polling is visibility-aware, non-overlapping, adaptive, and state-change guarded.
3. Update `patch/modules/cats/CatPet.tsx` and `CatPet.css` so frame-by-frame position changes use CSS transform through a ref instead of React position state.
4. Update relevant README/performance docs.
5. Run frontend build and focused source checks.
6. Mark the todo complete only after commit, push to `origin/main`, deploy, and smoke checks.

## verification plan
- `npm run build` from `frontend/web`.
- Source checks for polling constants, in-flight guard, visibility guard, and transform-based cat positioning.
- Deploy changed code and rebuilt dist to the server.
- Confirm API service is active and public endpoints return 200.
