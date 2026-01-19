# PGN v2 Ops Guide

## Purpose
Operational runbook for PGN v2 integrity, repair, and status interpretation.

## PGN status meanings
- `ready`: PGN artifacts are synced and metadata is up to date.
- `missing`: One or more R2 artifacts are missing (PGN/tree/fen).
- `mismatch`: Chapter `r2_key` does not match the expected key pattern.
- `error`: Sync or repair failed.

## Integrity scan
Run the scan and write auditable reports:

```bash
PGN_SCAN_OPERATOR=<name> ENV=<env> \
R2_ENDPOINT=<...> R2_ACCESS_KEY_ID=<...> R2_SECRET_ACCESS_KEY=<...> R2_BUCKET_NAME=<...> \
DATABASE_URL=<asyncpg> PYTHONPATH=.:backend \
.venv/bin/python backend/scripts/scan_pgn_integrity.py
```

Outputs:
- `docs/migration_reports/migration_scan_report.txt`
- `docs/migration_reports/migration_scan_summary.json`
- `docs/migration_reports/migration_acceptance.md`

## Repair a chapter
Use the unified repair path:

```python
await pgn_sync_service.sync_chapter_pgn(chapter_id)
```

Notes:
- When `PGN_V2_ENABLED=false`, the legacy sync path is used.
- Successful sync sets `pgn_status=ready`.

## Reading status in API
`pgn_status` is exposed on chapter list and detail responses:
- `GET /api/v1/workspace/studies/{study_id}`
- `GET /api/v1/workspace/studies/{study_id}/chapters/{chapter_id}`

## Logging and alerting
- Sync path: `backend/modules/workspace/domain/services/pgn_sync_service.py`
- API reads: `/show` and `/fen` endpoints in `backend/modules/workspace/api/endpoints/studies.py`
- Common log fields: `study_id`, `chapter_id`, `r2_key`, `error_code`
