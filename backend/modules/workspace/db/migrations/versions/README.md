## header
Created at: 2026-07-09 00:52 EDT
Created by: Codex
Last Modified at: 2026-07-09 00:52 EDT
Lst Modified by: Codex

## brief intro
- goal for this folder: Hold ordered Alembic revision files for workspace schema changes.
- 架构思路: Each file has a stable revision id, previous `down_revision`, and small upgrade/downgrade operations.

## folder structure
|-20260110_0000_initial_schema.py initial workspace tables.
|-20260227_0019_add_deleted_root_id_to_nodes.py recycle-bin grouping column.
|-20260709_0020_add_chapter_tree_revision.py chapter tree collaboration revision metadata.

## 代办
- Add one migration per production schema change; do not edit already-deployed historical migrations unless explicitly repairing a known bad migration.
