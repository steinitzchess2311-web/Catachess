# Stage 3A Runtime Validation

## Method
In-process FastAPI validation using `TestClient` (no socket binding allowed in this environment).

## Test identifiers
- study_id: `6b01808c-0321-4982-a2e6-a4b29541be81`
- chapter_id: `01KF783SN3E23VGQBVBQQJAK2K`
- node_id: `01KF7MM77TD1HGNF121Z4Y0B4A`

## Disabled state (PGN_V2_ENABLED=false)
- `/show` status: 404
- `/show` body: `{"detail":"PGN V2 endpoints are not enabled"}`
- `/fen` status: 404
- `/fen` body: `{"detail":"PGN V2 endpoints are not enabled"}`

## Enabled state (PGN_V2_ENABLED=true)
- `/show` status: 200
- `/show` body (truncated):
  - `{"headers":[{"k":"ChapterId","v":"01KF783SN3E23VGQBVBQQJAK2K"}, ...], "nodes": {...}, "render": [...]}`
- `/fen` status: 200
- `/fen` body:
  - `{"fen":"rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1","node_id":"01KF7MM77TD1HGNF121Z4Y0B4A","san":"e4","uci":"e2e4","move_number":1,"color":"white"}`

## Notes
- Verification table init logged errors (invalid DSN for sync tables); does not affect `/show`/`/fen` validation.
- Socket binding is not permitted in this environment, so in-process validation is used.
