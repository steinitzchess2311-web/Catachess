## header
Created at: 2026-07-09 00:52 EDT
Created by: Codex
Last Modified at: 2026-07-09 00:52 EDT
Lst Modified by: Codex

## brief intro
- goal for this folder: Own workspace database sessions, SQLAlchemy tables, repositories, and Alembic migrations.
- 架构思路: Keep database shape changes in `migrations/versions`, table declarations in `tables`, and data access in `repos`.

## folder structure
|-base.py SQLAlchemy base and timestamp mixins.
|-session.py async database initialization and FastAPI session dependency.
|-tables/ ORM table declarations for workspace entities.
|-repos/ repository layer for table-specific queries and persistence.
|-migrations/ Alembic migration environment and version scripts.

## 代办
- Continue keeping schema changes migration-first before endpoint code depends on new columns.
