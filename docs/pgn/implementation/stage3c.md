# Stage 3C - Performance and Capacity Validation

## Constraints (must be at top of every stage doc)
- [ ] Each completed task must have its checkbox ticked.
- [ ] If blocked or uncertain, state the problem directly; do not guess then tick.
- [ ] No ticking before work is done.
- [ ] No false progress; spot checks will compare with code.

---

## Goal (product-level)
Validate PGN v2 performance under real load: import, render, and analysis.

Key invariant: Postgres node tree is the truth, R2 artifacts are derived; performance must not break the sync chain.

---

## Checklist

### A. Import performance
- [ ] Use a large PGN dataset (>10MB, >500 chapters).
  - Use existing generator or sample in `docs/performance_reports/`.
- [ ] Measure import time and peak memory.
  - Import path: `backend/modules/workspace/domain/services/chapter_import_service.py`
  - Entry points:
    - `import_pgn()` in `backend/modules/workspace/api/endpoints/studies.py`
- [ ] If slow, identify bottleneck:
  - Parser: `backend/core/real_pgn/parser.py`
  - Adapter: `modules/workspace/pgn_v2/adapters.py`
  - DB inserts: `VariationRepository.create_variation()`

### B. Render performance (frontend)
- [ ] Render deep variations (5+ levels) using ShowDTO.
  - API: `/show` -> `backend/modules/workspace/api/endpoints/studies.py`
  - Frontend: `frontend/ui/modules/study/events/index.ts`
- [ ] Record time to first render and interaction latency.
- [ ] If slow, consider:
  - Reducing token volume in `backend/core/real_pgn/show.py`
  - Lazy rendering or chunked render in `events/index.ts`

### C. FEN/analysis throughput
- [ ] Generate fen_index from node tree.
  - `backend/core/real_pgn/fen.py`
  - Upload via `PgnV2Repo.save_fen_index()`
- [ ] Run tagger/engine on fen_index in batch.
  - Existing entry: `backend/core/tagger/analysis/pipeline.py`
  - If needed, add `fen_processor` to read `fen_index.json`.

### D. Performance thresholds (targets)
- [ ] Import single chapter < 2s
- [ ] Frontend render < 300ms
- [ ] Tagger per 100 nodes < 5s

---

## Verification steps
- Store timing logs in `docs/performance_reports/`.
- Include hardware/environment details.
- Record sample study_id/chapter_id tested.

---

## Output (deliverables)
- Performance report
- Optimization list if thresholds missed
- Clear go/no-go decision
