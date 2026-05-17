# Catachess

Catachess is a chess learning product with a FastAPI backend, a React/Vite web frontend, and patch modules for study editing, live games, classrooms, and training tools.

## Runtime Architecture

- Backend: `backend/`, FastAPI APIs and shared chess/domain modules.
- Frontend: `frontend/web/`, React + Vite application deployed through the web build pipeline.
- Product modules: `patch/modules/`, feature slices that are mounted by the frontend or backend.
- Tests: `tests/` and module-local `*/tests/` folders.
- Documentation: every actively maintained folder should carry a `README.md` that explains responsibility, important files, and test commands.

## Deployment Notes

- Frontend deployment is connected to GitHub/Cloudflare.
- Backend deployment is connected to Railway.
- Database-backed features must treat the deployed database as the source of truth.
- Before restarting any target-machine service, first verify that no user is currently playing a game. Do not interrupt live games.

## Current Product Invariants

- A workspace study is both a `nodes` row with `node_type=study` and a `studies` row.
- Every newly created study must contain one ready default chapter titled `Chapter 1`.
- Chapter move trees are stored as `tree.json` objects in R2; the SQL row stores metadata and the R2 key.
- Frontend `username` is a display/game identity, not the JWT subject UUID. UUID belongs in `userId`.
- Live-game APIs use the player id string supplied by the UI. Passing a UUID after a game was created with a username changes the player's identity and breaks reconnect/current-game lookups.

## Local Commands

```bash
# Frontend production build
cd frontend/web
npm run build

# Backend syntax check for touched workspace files
cd ../..
PYTHONPATH=backend python -m py_compile \
  backend/modules/workspace/domain/services/default_chapter_service.py \
  backend/modules/workspace/api/endpoints/nodes.py \
  backend/modules/workspace/api/endpoints/studies.py
```

The local Python test environment may need a working arm64-compatible dependency set before `pytest` can run on Apple Silicon.

## Documentation Map

- `backend/modules/workspace/README.md`: workspace backend module, study/chapter rules, API seams.
- `frontend/web/README.md`: web app ownership, identity handling, build verification.
- `patch/modules/user_games/README.md`: live-game frontend identity contract.
- `CONTEXT.md`: product-domain glossary shared by code and docs.
