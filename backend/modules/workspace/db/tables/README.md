## header
Created at: 2026-07-09 00:52 EDT
Created by: Codex
Last Modified at: 2026-07-09 00:52 EDT
Lst Modified by: Codex

## brief intro
- goal for this folder: Declare SQLAlchemy ORM tables used by the workspace module.
- 架构思路: Tables mirror Alembic migrations and expose only schema-level behavior; business rules live in services and policies.

## folder structure
|-nodes.py workspace node table.
|-studies.py study and chapter tables.
|-acl.py ACL and share link tables.
|-events.py workspace event table.
|-variations.py legacy move tree tables.

## 代办
- Keep table declarations synchronized with every migration that adds or removes columns.
