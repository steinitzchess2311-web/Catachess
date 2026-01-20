Stage 02 - Idempotency + Permissions

Goal
- Ensure default chapter creation is idempotent and permission-safe.

Must-reference paths
- Legacy chapter create/list endpoints
- Patch entry flow (study entry handler)

Constraints
- No duplicate chapters on concurrent entry.
- Permission denial should not create chapters.

Checklist
- [ ] Use legacy "get chapters" as the source of truth (do not cache locally).
- [ ] Implement idempotent create: if create fails with "already exists", refetch list.
- [ ] If permissions fail, stop entry and display error.
- [ ] Ensure patch does not write tree.json if chapter creation failed.
- [ ] Write completion report in patch/docs/chapter_fix/summary/ChapterFix_stage02.md.
