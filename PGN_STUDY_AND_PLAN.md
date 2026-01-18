PGN Study Summary and Plan
==========================

Sources used
------------
- Chessprogramming wiki: Portable Game Notation (PGN) overview.
  https://www.chessprogramming.org/Portable_Game_Notation
- The wiki links to the PGN standard repo and Wikipedia for details.

PGN format summary (relevant to our study/variation/comment workflow)
---------------------------------------------------------------------
1) Tag pairs (headers)
   - Each header is one line: [Tag "Value"]
   - Common tags: Event, Site, Date, Round, White, Black, Result
   - Starting position uses:
     - [SetUp "1"]
     - [FEN "fen-string-here"]
   - Tags are separated from movetext by a blank line.

2) Movetext (SAN)
   - Moves are written in SAN with move numbers:
     - "1. e4 e5 2. Nf3 Nc6"
   - Results at the end:
     - "1-0", "0-1", "1/2-1/2", or "*"

3) Variations
   - Parentheses introduce variations:
     - "1. e4 (1. d4 d5) e5"
   - Variations can nest:
     - "( ( ... ) ... )"
   - Variations are part of the same PGN text and do not require a
     separate table in the database.

4) Comments
   - Braces add comments for a move:
     - "1. e4 {This is a comment} e5"
   - Comments can appear after any SAN move and are stored inline.

5) NAGs (annotation glyphs)
   - Can appear as symbols or $ codes:
     - "Nf3 !" or "Nf3 $1"
   - They are part of movetext and belong in the same PGN string.

How this applies to our current code
------------------------------------
- We already have a full PGN parser + serializer under:
  - backend/modules/workspace/pgn/serializer/to_tree.py
  - backend/modules/workspace/pgn/serializer/to_pgn.py
- There is a PGN cleaner + clipper pipeline in:
  - backend/modules/workspace/pgn/cleaner/
- Chapter PGN is already stored in R2 under:
  - backend/modules/workspace/storage/keys.py (chapters/{id}.pgn)
- The current variation table is not needed if we treat the PGN as the
  single source of truth and mutate it directly.

Plan (based on current code state)
---------------------------------
Goal: Store all moves, variations, and comments in PGN (R2) and stop
using the variations table for study editing.

Step 1: Add a PGN mutation service (backend)
- Create a new service in backend/modules/workspace/domain/services/
  e.g. pgn_edit_service.py.
- Inputs:
  - chapter_id
  - base_pgn (download from R2)
  - action: add_move / add_variation / add_comment / add_nag
  - move_path: identifies the node in the PGN tree (mainline or variation)
  - move data (UCI or SAN, plus optional promotion)
- Flow:
  1) Load PGN from R2 (chapter pgn).
  2) pgn_to_tree() -> VariationNode tree.
  3) Apply mutation to the tree (insert new child, edit comment, add NAG).
  4) tree_to_pgn() to write back.
  5) Upload to R2 (same chapter key).
  6) Return updated pgn + updated move list if needed.

Step 2: Define a stable move path format
- Use an explicit path string for variations, similar to:
  - "main.12" (12th ply in mainline)
  - "main.12.v1.4" (variation 1 at ply 12, then 4 plies into that line)
- This should map directly to the VariationNode tree traversal.
- This can reuse existing move_path logic from pgn_cleaner clipping.

Step 3: Replace variation endpoints
- Replace or deprecate:
  - /api/v1/workspace/studies/{id}/chapters/{id}/moves
  - /api/v1/workspace/studies/{id}/chapters/{id}/moves/{move_id}/annotations
- New endpoints that edit the PGN in R2:
  - POST /api/v1/workspace/chapters/{id}/pgn/move
  - POST /api/v1/workspace/chapters/{id}/pgn/variation
  - POST /api/v1/workspace/chapters/{id}/pgn/comment
  - POST /api/v1/workspace/chapters/{id}/pgn/nag
- Each endpoint should return updated PGN and/or resolved FEN for the
  current ply to keep UI in sync.

Step 4: Frontend wiring
- Study UI should:
  - Use PGN-only endpoints for move/variation/comment.
  - On drag move:
    1) compute UCI in the client
    2) call PGN edit endpoint
    3) refresh chapter PGN + move tree
- Comments should call the PGN comment endpoint with move_path.
- Remove usage of variation table endpoints and move_id for annotations.

Step 5: PGN/FEN pipeline
- Keep using /api/games/pgn/fen for board updates, but clamp ply and
  ensure SetUp+FEN are handled.
- If a PGN starts from custom FEN, use SetUp/FEN tags when saving.

Step 6: Tests
- Add service tests in backend/modules/workspace/tests/:
  - Apply move into mainline.
  - Insert variation at ply.
  - Add comment and verify { } appears in output.
  - Verify nested variations are preserved.

Notes / constraints
-------------------
- The existing parser/serializer already supports variations and comments.
- The chapter splitter is already implemented; keep it.
- Once PGN is the single source of truth, the variation table can be
  deprecated or left unused.
