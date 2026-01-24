# Environment Contract (Postgres + R2 + Engine)

This file defines the minimum environment variables required to run
PGN v2 end-to-end (Postgres + R2 + Engine). It also lists the code
paths that read each variable./

## 1) Postgres (workspace data)

Required:
- DATABASE_URL
  - Example: postgresql+asyncpg://user:pass@host:5432/dbname
  - Used by:
    - backend/core/config.py (settings.DATABASE_URL)
    - backend/modules/workspace/main.py
    - backend/modules/workspace/db/migrations/env.py

Notes:
- This is the ONLY required Postgres variable for workspace DB.

## 2) R2 (PGN and artifacts)

There are two R2 env naming schemes in the repo. Both are used.

### 2.1 Workspace R2 client (modules/workspace/storage/r2_client.py)
Required:
- R2_ENDPOINT
- R2_ACCESS_KEY
- R2_SECRET_KEY
- R2_BUCKET

Used by:
- backend/modules/workspace/storage/r2_client.py
- backend/modules/workspace/domain/services/pgn_sync_service.py
- backend/modules/workspace/domain/services/chapter_import_service.py

### 2.2 Scan script (backend/scripts/scan_pgn_integrity.py)
Required:
- R2_ENDPOINT
- R2_ACCESS_KEY_ID
- R2_SECRET_ACCESS_KEY
- R2_BUCKET_NAME

Used by:
- backend/scripts/scan_pgn_integrity.py

### 2.3 Core storage (backend/storage/core/config.py)
Alternative prefixes supported:
- GAME_STORAGE_R2_ENDPOINT
- GAME_STORAGE_R2_BUCKET
- GAME_STORAGE_R2_ACCESS_KEY_ID
- GAME_STORAGE_R2_SECRET_ACCESS_KEY

Fallbacks also accept:
- R2_ENDPOINT
- R2_BUCKET
- R2_ACCESS_KEY_ID
- R2_SECRET_ACCESS_KEY

Used by:
- backend/storage/core/config.py

## 3) Engine / Tagger

Required for tagger/engine analysis:
- ENGINE_URL (default: https://sf.cloudflare.com)

Used by:
- backend/core/chess_engine/__init__.py
- backend/core/tagger/facade.py
- backend/core/tagger/analysis/pipeline.py

## 4) PGN v2 feature flag

Optional:
- PGN_V2_ENABLED (true/false)

Used by:
- backend/core/config.py
- backend/modules/workspace/api/endpoints/studies.py
- backend/modules/workspace/domain/services/pgn_sync_service.py

## 5) Quick sanity checks

Postgres:
- Print DATABASE_URL: echo $DATABASE_URL

R2 (workspace client):
- echo $R2_ENDPOINT
- echo $R2_ACCESS_KEY
- echo $R2_SECRET_KEY
- echo $R2_BUCKET

R2 (scan script):
- echo $R2_ENDPOINT
- echo $R2_ACCESS_KEY_ID
- echo $R2_SECRET_ACCESS_KEY
- echo $R2_BUCKET_NAME

Engine:
- echo $ENGINE_URL

PGN v2:
- echo $PGN_V2_ENABLED

