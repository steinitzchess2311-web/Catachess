# Explorer Player Color Filter Requirements

## Header
Created at: 2026-07-08 18:30 EDT
Created by: Codex
Last Modified at: 2026-07-08 18:43 EDT
Last Modified by: Codex

## Requirements
- When one or more player filters are active, hide the year filter UI completely.
- Remove the "Year filters paused" explanatory message.
- When no player filter is active, the year filter lower bound and placeholder must start at the database's earliest valid game year, not 1995.
- Add a player side segmented control with:
  - `All`
  - `White`
  - `Black`
- The side control appears only when a player filter is active.
- The side control filters both move statistics and the position game list.
- Preserve existing player spelling variant behavior.
- Preserve sort controls and game list pagination.
