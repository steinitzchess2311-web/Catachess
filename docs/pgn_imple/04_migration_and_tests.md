# Migration and Tests

Restraints (check off when done)
--------------------------------
- [x] Each step below is completed and marked with [x].
- [x] Newly created code files are each <= 100 lines.
- [x] New code is placed in the correct folder.

Step 1: Dual-run phase (safe rollout)
-------------------------------------
- [x] Add a feature flag (env) for new detector (`NEW_PGN_DETECTOR_ENABLED`).
- [x] Run both detectors and log differences (`NEW_PGN_DETECTOR_DUAL_RUN`).
- [x] Do not alter stored PGN during this phase.

Step 2: Replace old detector usage
----------------------------------
- [x] Update all uses of `modules/workspace/pgn` for detection:
  - [x] Chapter import splitter.
  - [x] Any new PGN upload endpoints.
- [x] Remove legacy detector from code paths after parity checks.

Step 3: Tests (backend)
-----------------------
- [x] Add tests in `tests/workspace/unit/pgn/`:
  - [x] Single game with headers.
  - [x] Multi-game PGN.
  - [x] Missing headers (returns empty list).
  - [x] Custom FEN headers preserved.

Step 4: Tests (frontend)
------------------------
- [x] Add a UI test or minimal integration test that (see `tests/workspace/integration/test_chapter_import_service.py`):
  - [x] Imports a multi-game PGN and confirms game count.
  - [x] Ensures UI does not crash on missing headers.

Step 5: Cutover
---------------
- [x] Remove old detector references.
- [x] Delete feature flag after stable period.
