# Explorer Player Color Filter Plan

## Header
Created at: 2026-07-08 18:30 EDT
Created by: Codex
Last Modified at: 2026-07-08 18:30 EDT
Last Modified by: Codex

## Requirement Reference
- `docs/requirements/explorer_player_color_filter.md`

## Plan
- Extend Explorer frontend types with `PlayerColorFilter = any | white | black`.
- Add `playerColor` state in `ExplorerPanel`.
- Hide `FilterBar` when players are selected; keep year filters for non-player database exploration.
- Add a compact side segmented control to `PlayerFilterRow`.
- Pass `player_color` to `fetchMasters` and `fetchMastersGames`.
- Extend server Explorer `/masters` player-filtered path with `player_color`.
- Extend server `/masters/games` query with the same `player_color` filter.
- Verify API counts differ for all/white/black and run frontend build.
