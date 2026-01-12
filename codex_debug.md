# Codex Debug Report

Date: 2026-01-11

## Scope
- Investigated backend test collection failures and missing imports.
- Focused on workspace permission/search modules and tagger import paths.
- Verified game storage additions compile under current layout.

## Changes Applied
- Fixed tagger import paths to use `core.tagger` instead of `backend.core.tagger`.
- Added root `conftest.py` to put `backend/` on `sys.path` for tests.
- Allowed extra env vars in `backend/core/config.py` to avoid hard failures on `R2_*` workspace env vars.
- Added missing permission helper `can_read` and conversion helpers in `workspace.domain.policies.permissions`.
- Updated `SearchService` to use the new `can_read` signature.
- Added compatibility re-export modules:
  - `backend/modules/workspace/db/tables/acls.py`
  - `backend/modules/workspace/db/tables/discussions.py`
- Fixed notification rule event constant to `EventType.DISCUSSION_THREAD_CREATED`.
- Added `get_pgn_clip_service` dependency to `workspace.api.deps`.

## Tests Run
- `./venv/bin/pytest backend`

## Test Result Summary
The backend test run now collects 318 tests but still fails heavily:
- 75 failed, 73 errors, 169 passed, 1 skipped (timeout after 120s).
- Failures concentrate in `backend/modules/workspace/tests/*` and appear pre-existing:
  - Permission enforcement and discussion API tests failing.
  - Search indexer tests failing due to signature mismatch (`SearchIndexer.__init__` expects more repos).
  - PGN cleaner/clip tests failing (logic issues).
  - Notification API/dispatcher tests failing (fixture errors).
  - Async fixture warnings in strict asyncio mode.

## Known Remaining Issues (Not Fixed)
- Workspace permission logic and discussion permission tests are failing broadly.
- Search indexer constructor signature mismatch vs tests.
- Multiple PGN cleaner/clip test failures (logic).
- Notification tests fail due to fixture/async setup.
- Some async fixtures are not marked/handled under strict asyncio mode.

## Notes
- I addressed import/module wiring to enable test collection and reduce startup failures.
- The remaining failures appear to be functional gaps or test mismatches unrelated to the recent game storage/R2 work.
