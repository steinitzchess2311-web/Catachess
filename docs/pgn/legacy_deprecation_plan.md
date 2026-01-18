# Legacy Deprecation Plan

## Scope
- Legacy serializer modules: `backend/modules/workspace/pgn/serializer/*`
- Legacy mainline endpoint: `/api/v1/workspace/studies/{study_id}/chapters/{chapter_id}/moves/mainline`

## Status
- Serializer modules marked deprecated with warnings.
- Endpoint marked deprecated in OpenAPI via `deprecated=True`.
- `backend/core/chess_basic/pgn/*` usage limited to game/session services (no study module imports found).

## Policy
- New code must not depend on `backend/modules/workspace/pgn/serializer`.
- All new study rendering should use `/show` and `/fen`.

## Removal prerequisites
- PGN v2 rollout complete and validated.
- Migration and integrity scan reports complete.
- Performance benchmarks meet Stage 3C thresholds.
