# Stage 3B Migration Acceptance Record

## Execution summary
- Scan command: `PYTHONPATH=.:backend DATABASE_URL=<asyncpg> R2_* .venv/bin/python backend/scripts/scan_pgn_integrity.py`
- Output: `docs/migration_reports/migration_scan_report.txt`
- Execution date: 2026-01-18T20:18:44.053489
- Operator: catadragon
- Environment: dev
- Host: 
- Total chapters scanned: 85
- Chapters without moves: 83
- R2 key mismatches: 0
- R2 missing PGN: 0
- R2 missing tree JSON: 0
- R2 missing FEN index: 0
- PGN sync failures: 0
- Resync attempts: 0
- Resync success: 0
- Resync failures: 0
- Chapters repaired (via resync): 0

## PGN status updates
- ready: 0
- missing: 0
- mismatch: 0
- error: 0

## Acceptance status
- Pending manual review of scan output.
