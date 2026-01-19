# Legacy PGN API (Deprecated)

## Status
Deprecated. Use PGN v2 `/show` and `/fen` endpoints instead.

## GET /api/v1/workspace/studies/{study_id}/chapters/{chapter_id}/moves/mainline
Deprecated endpoint for mainline-only rendering.

## Deprecation notice
- This endpoint will be removed in a future release.
- Retirement phase: `/moves/mainline` is in retirement and should not be used by new clients.
- Removal target: see `docs/pgn/deprecation_timeline.md` (Jan. 18 6pm EST).
- New code should not depend on legacy serializers under `backend/modules/workspace/pgn/serializer`.
