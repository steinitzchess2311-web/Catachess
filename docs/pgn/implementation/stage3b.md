# Stage 3B - Data Migration and Consistency Validation (Full Sweep)

## Constraints (must be at top of every stage doc)
- [ ] Each completed task must have its checkbox ticked.
- [ ] If blocked or uncertain, state the problem directly; do not guess then tick.
- [ ] No ticking before work is done.
- [ ] No false progress; spot checks will compare with code.

---

## Goal (product-level)
Ensure Postgres chapter nodes and R2 PGN artifacts are aligned by `chapter_id`.

Key invariant: chapter_id is the alignment key between Postgres (variation tree) and R2 (PGN/tree/fen_index).

---

## Checklist

### A. Alignment rules (must match code)
- [ ] Rule 1: `chapters.r2_key` must equal `R2Keys.chapter_pgn(chapter_id)`.
  - File: `modules/workspace/storage/keys.py`
  - Function: `R2Keys.chapter_pgn(chapter_id)`
- [ ] Rule 2: If any R2 artifact missing -> resync from Postgres variations.
  - File: `backend/modules/workspace/domain/services/pgn_sync_service.py`
  - Function: `sync_chapter_pgn()`
  - Uses DB (Variation + MoveAnnotation) as truth.
- [ ] Rule 3: If metadata missing (hash/size/etag), resync.

### B. Scan script (required)
- [ ] File: `backend/scripts/scan_pgn_integrity.py`
- [ ] Ensure the scan uses chapter_id as key and checks R2 artifacts.
  - Imports to verify:
    - `from modules.workspace.db.repos.study_repo import StudyRepository`
    - `from modules.workspace.db.repos.variation_repo import VariationRepository`
    - `from modules.workspace.pgn_v2.repo import PgnV2Repo, validate_chapter_r2_key, backfill_chapter_r2_key`
    - `from modules.workspace.storage.keys import R2Keys`
- [ ] Ensure scan iterates all chapters:
  - `chapters = await study_repo.get_all_chapters()`
- [ ] Ensure scan fixes `r2_key` mismatch:
  - `if not validate_chapter_r2_key(...): chapter.r2_key = backfill_chapter_r2_key(chapter); await study_repo.update_chapter(chapter)`
- [ ] Ensure scan checks R2 artifacts by chapter_id:
  - `pgn_v2_repo.exists_pgn(chapter_id)`
  - `pgn_v2_repo.exists_tree_json(chapter_id)`
  - `pgn_v2_repo.exists_fen_index(chapter_id)`
- [ ] Ensure scan triggers resync on missing artifacts:
  - `await pgn_sync_service.sync_chapter_pgn(chapter_id)`

### C. Output report (required)
- [ ] Store scan output in `docs/migration_reports/`.
- [ ] Required fields:
  - `total_chapters_scanned`
  - `r2_key_mismatches`
  - `r2_missing_pgn`
  - `r2_missing_tree_json`
  - `r2_missing_fen_index`
  - `chapters_repaired`
  - `pgn_sync_failures`

### D. Acceptance criteria (required)
- [ ] `r2_key` mismatches == 0
- [ ] All missing artifacts either resynced or explicitly documented as missing
- [ ] Record operator name + date in `docs/migration_reports/migration_acceptance.md`

---

## Verification steps
- Run scan script in the target environment.
- Confirm R2 artifacts exist for chapters with variations.
- Confirm frontend uses API only (no R2 key composition).

---

## Output (deliverables)
- Full scan report
- Repair log
- Migration acceptance record
