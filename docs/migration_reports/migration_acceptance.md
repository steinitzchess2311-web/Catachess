# Stage 3B Migration Acceptance Record

## Execution summary
- Scan command: `PYTHONPATH=.:backend DATABASE_URL=<asyncpg> R2_* .venv/bin/python backend/scripts/scan_pgn_integrity.py`
- Output: `docs/migration_reports/migration_scan_report.txt`
- Total chapters scanned: 85
- Chapters without moves: 83
- R2 key mismatches: 0
- R2 missing PGN: 0
- R2 missing tree JSON: 0
- R2 missing FEN index: 0
- PGN sync failures: 0
- Chapters repaired (via resync/backfill): 0

## Findings
- Illegal SAN fixed and rescan clean (see `docs/migration_reports/illegal_san_fix.md`).
- Chapters without moves (83) do not require tree/fen artifacts.
- Show/FEN consistency validation recorded in `docs/migration_reports/migration_validation_details.md` (2 chapters with variations).
- PGN round-trip on sample vectors shows normalized mismatches (see same report).

## Repairs performed
- Legacy resync attempted for all missing artifacts (no failures reported).

## Acceptance status
- Accepted for R2 integrity (no missing artifacts for chapters with moves).
- PGN round-trip parity still requires follow-up (normalized_match=false on samples).
