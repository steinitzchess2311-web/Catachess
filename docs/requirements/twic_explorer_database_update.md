## header
Created at: 2026-07-08 16:54:53 EDT
Created by: Codex
Last Modified at: 2026-07-08 16:54:53 EDT
Lst Modified by: Codex

## brief intro
- goal for this file: Define the requested Explorer database refresh from The Week in Chess.
- 架构思路: Treat the Explorer database as production data: inspect current coverage, download missing upstream PGN issues, deduplicate, rebuild side indexes, then swap atomically.

## requirements
- Determine current production Explorer coverage before importing.
- Use the latest TWIC archive state as the upstream source.
- Do not re-import already indexed games into additive RocksDB statistics.
- Preserve existing `database.catachess.com` endpoints during long rebuild work.
- Keep rollback available for the live DuckDB index.
- Verify health and basic Explorer responses after the update.
