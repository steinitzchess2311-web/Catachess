## header
Created at: 2026-07-08 16:54:53 EDT
Created by: Codex
Last Modified at: 2026-07-08 16:54:53 EDT
Lst Modified by: Codex

## topic twic explorer database update

1. What is the data source?
The production Explorer uses The Week in Chess PGN files for its masters database.

2. What is current production state?
The live DuckDB index has 4,620,978 games and 380,904,686 positions; the raw PGN snapshot tail reaches early February 2026.

3. What is latest upstream issue?
The TWIC archive lists TWIC 1652 dated 2026-07-06 with a PGN download at `https://theweekinchess.com/zips/twic1652g.zip`.

4. What is the major risk?
RocksDB move statistics are additive, so re-importing already indexed TWIC files can double-count positions. The update must deduplicate before writing production indexes.

5. What is the safe path?
Download missing issue PGNs, filter/import only game IDs that are absent from the live index, rebuild DuckDB in a side file, then perform a brief atomic swap with rollback.
