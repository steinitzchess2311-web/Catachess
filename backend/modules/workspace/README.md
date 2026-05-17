# Workspace Backend Module

FastAPI workspace backend for chess study organization, study chapters, PGN/tree storage, permissions, discussions, notifications, search, versions, and presence.

## Module Shape

- `api/`: FastAPI schemas, dependencies, REST endpoints, and WebSocket entrypoints.
- `db/`: SQLAlchemy tables, repositories, and async session setup.
- `domain/`: business models, policies, and services.
- `events/`: event bus and subscribers for audit/search/notification side effects.
- `pgn/` and `pgn_v2/`: PGN parsing, serialization, cleaner/export logic.
- `storage/`: Cloudflare R2/S3-compatible object storage client and key rules.
- `tests/`: module-level API, service, event, and policy tests.

## Study And Chapter Invariants

- A study is represented by a `nodes` row with `node_type=study` and a matching `studies` row.
- Every newly created study must have one default chapter titled `Chapter 1`.
- Both study creation APIs must preserve that invariant:
  - `POST /studies`
  - `POST /nodes` with `node_type=study`
- Default chapter creation lives in `domain/services/default_chapter_service.py` so both API paths share the same implementation.
- A chapter has SQL metadata in `chapters` and a `tree.json` object in R2 at `R2Keys.chapter_tree_json(chapter_id)`.
- `studies.chapter_count` must match the number of chapter rows.

## API Entry Points

- `api/endpoints/nodes.py`: workspace/folder/study node CRUD, move/delete/trash behavior.
- `api/endpoints/studies.py`: study metadata, chapters, moves, PGN import/export, tree migration helpers.
- `api/endpoints/users.py`: workspace user lookup helpers.
- `api/router.py`: module router composition.

## Storage Contract

- SQL stores metadata and R2 keys.
- R2 stores large tree/PGN/snapshot payloads.
- New empty chapters write a valid tree payload with:
  - `version: v1`
  - `rootId: root`
  - one root node with no children
  - `meta.result: *`

## Test Commands

```bash
PYTHONPATH=backend pytest backend/modules/workspace/tests/test_api_nodes.py -q
PYTHONPATH=backend python -m py_compile \
  backend/modules/workspace/domain/services/default_chapter_service.py \
  backend/modules/workspace/api/endpoints/nodes.py \
  backend/modules/workspace/api/endpoints/studies.py
```

If local `pytest` loads an incompatible `pydantic_core` wheel, rebuild the Python environment for the machine architecture before treating backend tests as meaningful.
