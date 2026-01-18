# Stage 3C Performance Report

## A. Import performance
- Dataset: `docs/performance_reports/large_pgn_generated.pgn` (12,094,690 bytes, 600 games; synthetic comment-heavy PGN).
- Import method: in-process `TestClient` to `/api/v1/workspace/studies/{study_id}/chapters/import-pgn`.
- Result: import did not complete within 300s (timed out). Multiple folders/studies were created before timeout (see log).
- Log: `docs/performance_reports/import_perf.log`.

## B. Render performance
- Blocked: requires browser Performance panel and UI runtime.

## C. Tagger/Engine load
- Input: mainline-only FEN index built from chapter `01KF783SN3E23VGQBVBQQJAK2K`.
- Result: `positions=1`, `errors=0`.
- Timing/RSS: see `/usr/bin/time` output in `docs/performance_reports/tagger_perf.log` (elapsed 2.93s, max RSS 69MB).
  - Note: full-tree FEN build failed due to illegal SAN in DB; mainline-only fallback used.

## D. Thresholds
- Import: >300s (timed out) for 12MB/600-game dataset.
- Render: not measured.
- Tagger: only 1 position measured.

## Follow-up required
- Provide UI runtime + browser profiling for render performance.
- Re-run import test until completion (current run timed out at 300s).
- Expand tagger test to 100+ positions for stable throughput.
