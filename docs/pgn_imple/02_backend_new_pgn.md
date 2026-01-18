# Backend Plan: New PGN Detector

Restraints (check off when done)
--------------------------------
- [x] Each step below is completed and marked with [x].
- [x] Newly created code files are each <= 100 lines.
- [x] New code is placed in `backend/core/new_pgn/`.

Step 1: Define the new data model
---------------------------------
- [x] Create `backend/core/new_pgn/types.py` with:
  - [x] `PGNHeader` map type alias.
  - [x] `PGNGame` dataclass (headers, movetext, raw, index).
  - [x] Keep this file under 100 lines.

Step 2: Implement a strict parser
---------------------------------
- [x] Create `backend/core/new_pgn/detector.py` (replace placeholder).
  - [x] Split by headers using `[Tag "Value"]` lines.
  - [x] Preserve raw lines for each game block.
  - [x] Extract movetext after the header section.
  - [x] If no headers found, return an empty list.
  - [x] Keep this file under 100 lines.

Step 3: Normalize input
-----------------------
- [x] Create `backend/core/new_pgn/normalize.py`.
  - [x] Ensure line endings are LF.
  - [x] Trim trailing whitespace but preserve content.
  - [x] Keep this file under 100 lines.

Step 4: Public API for detector
-------------------------------
- [x] Create `backend/core/new_pgn/api.py`.
  - [x] `detect_games(pgn_text: str) -> list[PGNGame]`.
  - [x] Call normalize + detector.
  - [x] Keep this file under 100 lines.

Step 5: Hook into backend endpoints
-----------------------------------
- [x] Add a new endpoint in `backend/routers/game_storage.py` or
      `backend/modules/workspace/api/`:
  - [x] `POST /api/games/pgn/detect` -> returns game count and headers.
  - [x] Use the new `detect_games` API.
  - [x] Update router registration if needed.

Step 6: Split into multiple studies and folder (n > 64)
-------------------------------------------------------
- [x] If detected games > 64:
  - [x] Split into `ceil(n/64)` studies.
  - [x] Create a folder node to contain those studies.
  - [x] Reuse existing workspace folder/study creation services.
  - [x] Return a payload from the study import endpoints (not detect) that includes:
    - [x] `was_split: true`
    - [x] `folder_id`
    - [x] list of created study IDs

Step 7: Connect to existing workspace services
----------------------------------------------
- [x] Wire to current study import pipeline so it:
  - [x] Uses the new detector output for chapters.
  - [x] Reuses the existing R2 chapter PGN storage.
  - [x] Updates node tree and study records consistently.

Step 8: Logging and errors
--------------------------
- [x] Return clear 400s for empty PGN input.
- [x] Return 200 with empty list if input has no headers.

Supervisor review checklist
---------------------------
- [x] Verify steps 1-5 were actually implemented (worker marked complete).
- [x] Verify split+folder creation uses existing workspace services.
- [x] Confirm no new file exceeds 100 lines.
