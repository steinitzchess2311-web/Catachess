# PGN Rewrite Overview

Purpose
-------
Rewrite the PGN detector and editing pipeline from scratch under
`backend/core/new_pgn`, then connect it to backend API and frontend UI.

Restraints (check off when done)
--------------------------------
- [x] Each step below is marked with [x] when completed.
- [x] Newly created code files are each <= 100 lines.
- [x] New code is placed in the correct module (no random locations).
- [x] Pathways/hooks updated in both backend and frontend.

High-level deliverables
-----------------------
- [x] New PGN detector in `backend/core/new_pgn/` with clean interfaces.
- [x] Backend API endpoints that call the new detector
      (`POST /api/games/pgn/detect` in `backend/routers/game_storage.py`).
- [x] Frontend UI hooks updated to use the new endpoints.
- [x] Migration plan to stop using the old PGN detector once stable.
- [x] If chapters > 64, split into `ceil(n/64)` studies and create a folder
      to contain those studies (auto-built, no manual step).

Supervisor status
-----------------
- [x] 01_overview.md drafted by worker.
- [x] 02_backend_new_pgn.md drafted by worker.
- [x] Review 01/02 content for split+folder requirement and UI/API wiring.

Glossary
--------
- "Detector": splits multi-game PGN into individual games/chapters.
- "Movetext": the SAN move sequence, including variations and comments.

Notes for new contributors
--------------------------
- The new system should treat PGN as the single source of truth.
- Variations are encoded in PGN with parentheses, comments in `{}`.
- Chapter splitting should not require DB changes.
