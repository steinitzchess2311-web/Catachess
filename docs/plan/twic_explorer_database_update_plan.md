## header
Created at: 2026-07-08 16:54:53 EDT
Created by: Codex
Last Modified at: 2026-07-08 16:54:53 EDT
Lst Modified by: Codex

## brief intro
- goal for this file: Execution plan for refreshing the production Explorer TWIC database.
- 架构思路: Use the existing production patch-import architecture where safe, but add a deduplicated PGN preparation step before any additive RocksDB write.

## related requirement
- docs/requirements/twic_explorer_database_update.md

## plan
1. Inspect production Explorer service configuration, live DuckDB row counts, and raw PGN coverage.
2. Confirm the latest TWIC issue and download missing PGN ZIPs from the official archive.
3. Produce import PGNs containing only games whose deterministic IDs are absent from the current index.
4. Archive any stale `index.duckdb.new` file before rebuilding.
5. Run the existing patch importer in tmux so long rebuild work survives the shell.
6. Verify service health, row counts, and representative Explorer queries after swap.
