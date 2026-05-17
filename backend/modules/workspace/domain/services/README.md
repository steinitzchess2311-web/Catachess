# Workspace Domain Services

Business workflows for the workspace module.

## Responsibilities

- Keep write-side business rules out of FastAPI endpoint handlers.
- Coordinate repositories, storage clients, events, and policies.
- Provide testable seams for behavior that is shared by more than one API path.

## Important Services

- `node_service.py`: create, update, move, delete, and permission-check workspace nodes.
- `study_service.py`: move and annotation operations inside study chapters.
- `variation_service.py`: variation-tree editing rules.
- `chapter_import_service.py`: PGN import and multi-study splitting.
- `default_chapter_service.py`: shared invariant that a new study receives a ready `Chapter 1`.

## Default Chapter Rule

Use `ensure_default_chapter(...)` whenever code creates a new study row outside the import pipeline. It is idempotent: if chapters already exist, it returns the existing count without writing R2 or SQL.
