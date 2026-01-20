Chapter Fix Plan (Patch)

Goal
- Ensure entering a study always yields a valid chapterId for patch flow.
- Chapter authority comes from legacy backend (DB), patch does not invent IDs.

Constraints
- Do not change DB schema.
- R2 key format remains chapters/{chapter_id}.tree.json.
- tree.json is canonical for patch; legacy PGN is not required for patch writes.

Risks to avoid
- Duplicate default chapter creation (must be idempotent).
- Permission mismatch between legacy and patch routes.
- Inconsistent metadata (title/order/startFen) between legacy and patch UI.
- Missing tree.json causing patch load failure.

Strategy
- On study entry, call legacy API to fetch chapters.
- If none exist, call legacy create chapter (idempotent behavior).
- Use returned chapterId to load tree.json via patch API.
- If tree.json missing, create empty tree.json via patch API.

Chapter selection rules
- Sort by `order` asc.
- If `order` missing, fall back to `created_at` asc.
- If both missing, fall back to `id` asc.
- If chapters list missing or invalid, surface LOAD_ERROR (no silent fallback).

API response expectations
- Primary: `response.chapters`
- Fallbacks: `response.study.chapters`, `response.data.chapters`

Success Criteria
- Patch entry always has a valid chapterId.
- No duplicate default chapters from concurrent entry.
- Clear error if chapter creation fails.
