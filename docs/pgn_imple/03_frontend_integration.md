# Frontend Plan: PGN Detector Integration

Restraints (check off when done)
--------------------------------
- [x] Each step below is completed and marked with [x].
- [x] Newly created code files are each <= 100 lines.
- [x] New code is placed under `frontend/ui/`.

Step 1: Add client API helper
-----------------------------
- [x] Create `frontend/ui/modules/study/api/pgn.ts`.
  - [x] `detectPGN(pgnText: string)` calls `/api/games/pgn/detect`.
  - [x] Handle 400s with user-friendly errors.

Step 2: Update the import flow
------------------------------
- [x] In `frontend/ui/modules/study/events/index.ts`:
  - [x] On PGN import, call `detectPGN`.
  - [x] If >64 games:
    - [x] Call backend split+folder endpoint (new response from detector flow).
    - [x] Navigate to the created folder or workspace list.
    - [x] Show a notice with the number of created studies.
  - [x] If 1 game, proceed as usual.

Step 3: UI feedback
-------------------
- [x] Show a simple toast/alert that includes:
  - [x] Number of detected games.
  - [x] Event/White/Black summary if present.

Step 4: Pathways and hooks
--------------------------
- [x] Ensure API base path aligns with production:
  - [x] `/api/games/pgn/detect` (backend).
  - [x] Use existing auth headers.

Step 5: Connect with existing UI components
-------------------------------------------
- [x] Keep using study module UI:
  - [x] `frontend/ui/modules/study/layout/index.html`
  - [x] `frontend/ui/modules/study/events/index.ts`
- [x] Reuse workspace selection flow:
  - [x] `frontend/ui/modules/workspace/events/index.ts`
- [x] Do not bypass existing routing guards or storage helpers.
