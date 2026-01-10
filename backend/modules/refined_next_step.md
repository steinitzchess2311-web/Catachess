# Refined Next Steps - Tagger Core (catachess/backend/modules/tagger_core)

This is an updated, opinionated plan based on the current implementation and
the legacy reference in `ChessorTag_final/chess_imitator/rule_tagger_lichessbot/rule_tagger2/`.

## Ground Rules
- Do not modify code in `ChessorTag_final/`.
- Keep each tag in a single file under `tagger_core/legacy/tags/`.
- Keep files <= 150 lines (split when needed).
- Tests live under `catachess/tests/`.
- Use the Stockfish path configured in `catachess`.

## Snapshot (Verified in Tree)
- Core contracts exist: `TagContext`, `TagEvidence`, `TagResult`.
- Shared helpers implemented: `metrics.py`, `phase.py`, `contact.py`,
  `tactical_weight.py`, `control_helpers.py`, `tension_helpers.py`,
  `maneuver_helpers.py`, `prophylaxis_helpers.py`, `sacrifice_helpers.py`.
- Tag families implemented (41 total): meta (7), opening (2), exchange (3),
  structure (3), initiative (3), tension (4), maneuver (5), prophylaxis (5),
  sacrifice (9).
- `facade.tag_position()` wires all detectors and returns a full `TagResult`.

## Gaps vs Legacy / Plan
- Engine score normalization for black appears inconsistent in
  `legacy/engine/stockfish_client.py` (PovScore + manual flip).
- TagEvidence is produced but not surfaced in `TagResult.analysis_context`,
  so observability and gating diagnostics are missing.
- `TAG_PRIORITY` includes `structural_blockage`, but no detector or TagResult
  field exists; gating/postprocess would drift.
- Docs are stale (`IMPLEMENTATION_SUMMARY.md`, `example_usage.py`) and still
  reference a “first_choice-only” state and missing README/NEXT_STEPS.
- CoD tags, postprocess, and regression harness are still missing.
- Tests for newly added tags are thin; most tags lack targeted unit coverage.

## Checklist - Completed
- [x] Data contracts (`TagContext`, `TagEvidence`, `TagResult`)
- [x] Shared helpers (metrics, phase, contact, tactical_weight, control,
      tension, maneuver, prophylaxis, sacrifice)
- [x] Tag families: meta/opening/exchange/structure/initiative/tension/
      maneuver/prophylaxis/sacrifice
- [x] Facade integration for all implemented tags

## Checklist - Next (Priority Order)
1. [ ] Fix eval normalization for black + add tests for both colors.
2. [ ] Surface TagEvidence in `analysis_context` (per-tag evidence + gates).
3. [ ] Align `TAG_PRIORITY` with TagResult fields (add/remove mismatch).
4. [ ] Implement CoD tags (9 subtypes) and hook into facade.
5. [ ] Add golden-case regression harness vs legacy outputs.
6. [ ] Implement postprocess/gating layer (priority + conflicts).
7. [ ] Performance pass (reduce engine calls, caching).

## Concrete Next Actions
1. **Normalize engine scores**
   - Fix `legacy/engine/stockfish_client.py` to return a consistent POV.
   - Add tests in `catachess/tests/` for white/black moves.
2. **Evidence plumbing**
   - Capture each detector’s TagEvidence list in `facade.tag_position()`.
   - Store per-tag evidence in `TagResult.analysis_context["evidence"]`.
3. **Priority alignment**
   - Either implement `structural_blockage` or remove it from
     `config/priorities.py`.
4. **CoD implementation**
   - Port CoD gates from
     `ChessorTag_final/.../rule_tagger2/legacy/cod_detectors.py` into
     `tagger_core/legacy/tags/` files.
5. **Regression tests**
   - Mirror golden cases from `ChessorTag_final` into `catachess/tests/fixtures/`.
   - Build a diff test to compare tag outputs against legacy.

## Definition of Done (per tag)
- Fires with correct thresholds (actor POV consistent for both colors).
- Evidence includes gates + threshold values.
- Regression diff within acceptable tolerance.
- File remains <= 150 lines and has >=3 tests.
