# Stage 3A - Grey Rollout and Rollback (Frontend + Backend Switches)

## Constraints (must be at top of every stage doc)
- [ ] Each completed task must have its checkbox ticked.
- [ ] If blocked or uncertain, state the problem directly; do not guess then tick.
- [ ] No ticking before work is done.
- [ ] No false progress; spot checks will compare with code.

---

## Goal (product-level)
Safely enable PGN v2 (ShowDTO + FEN) in a grey rollout. Provide immediate rollback.

Key invariant: Postgres node tree is the source of truth, PGN artifacts live in R2, and chapter_id is the alignment key.

---

## Checklist

### A. Frontend switch (required)
- [ ] File: `frontend/ui/modules/study/api/pgn.ts`
- [ ] Verify default for `USE_SHOW_DTO` is `false` for grey rollout (do not enable globally).
  - Location: `export const USE_SHOW_DTO = (() => { ... return false; })();`
- [ ] Verify `toggleShowDTO()` exists and flips localStorage key.
  - Function: `toggleShowDTO()` in `frontend/ui/modules/study/api/pgn.ts`
  - localStorage key: `catachess_use_show_dto`
- [ ] Grey rollout policy written down: only internal/whitelist accounts enable ShowDTO.
  - Source of truth for whitelist: `docs/pgn/rollout_whitelist.md`.

### B. Backend switch (required)
- [ ] File: `backend/core/config.py`
- [ ] Add env flag `PGN_V2_ENABLED: bool = False` in `Settings`.
  - Import already present: `from pydantic_settings import BaseSettings` (verify existing pattern).
- [ ] Gate `/show` and `/fen` endpoints using `settings.PGN_V2_ENABLED`.
  - File: `backend/modules/workspace/api/endpoints/studies.py`
  - Imports to verify:
    - `from backend.core.config import settings`
    - `from fastapi import HTTPException, status`
  - Add at top of each endpoint:
    - `if not settings.PGN_V2_ENABLED: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PGN V2 endpoints are not enabled")`

### C. Frontend rendering fallback (required)
- [ ] File: `frontend/ui/modules/study/events/index.ts`
- [ ] Ensure ShowDTO load is conditional on `isShowDTOEnabled()`.
  - Imports:
    - `import { fetchShowDTO, isShowDTOEnabled } from '../api/pgn';`
- [ ] Verify fallback to legacy `/moves/mainline` when ShowDTO disabled or fails.
  - Check `currentShowDTO = null` path and fallback logic.

### D. Rollback plan (required)
- [ ] Frontend rollback:
  - Set `localStorage.setItem('catachess_use_show_dto', 'false')`.
  - Or remove key entirely to use default.
- [ ] Backend rollback:
  - Set `PGN_V2_ENABLED=false`.
  - `/show` and `/fen` return 404.
- [ ] Legacy sync rollback:
  - `backend/modules/workspace/domain/services/pgn_sync_service.py`
  - `sync_chapter_pgn()` must fall back to `sync_chapter_pgn_legacy()` when flag is false.

---

## Verification steps
- Frontend: toggle localStorage key and confirm the move tree renders using ShowDTO when enabled, and legacy when disabled.
- Backend: hit `/api/v1/workspace/studies/{study_id}/chapters/{chapter_id}/show` and `/fen/{node_id}`; verify 404 when disabled, 200 when enabled.
- Ensure no direct R2 access from frontend; all data comes via API.

---

## Output (deliverables)
- Dual switches (frontend + backend)
- Grey rollout policy documented
- Rollback steps documented and validated
