## header
Created at: 2026-07-09 00:52 EDT
Created by: Codex
Last Modified at: 2026-07-09 00:52 EDT
Lst Modified by: Codex

## brief intro
- goal for this folder: Store Alembic configuration for workspace database schema migrations.
- 架构思路: `env.py` wires SQLAlchemy metadata into Alembic, while `versions/` contains ordered reversible schema changes.

## folder structure
|-env.py Alembic runtime environment.
|-script.py.mako Alembic migration template.
|-versions/ ordered migration files.

## 代办
- Keep new production schema changes reversible and aligned with ORM table declarations.
