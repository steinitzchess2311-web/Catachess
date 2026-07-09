# Blog Product Redesign And Image Integrity Plan
Created at: 2026-07-09 01:05 EDT
Created by: Codex
Last Modified at: 2026-07-09 01:05 EDT
Last Modified by: Codex

## brief intro
- goal: Execute `docs/requirements/blog_product_redesign_and_image_integrity.md`.
- 架构思路: First harden the backend persistence path, then replace high-risk inline frontend styles with scoped product CSS, and finally verify through focused tests and build.

## plan
1. Audit current blog article create/update/upload and image linking code.
2. Add focused backend tests for image URL extraction, link/unlink behavior, and transaction failure behavior.
3. Make image link sync URL matching robust against encoded/unencoded URL forms.
4. Move article create/update image sync into the same database transaction as the article mutation.
5. Redesign `BlogsPage` shell, content area, article cards, category sidebar, and editor modal with scoped CSS classes.
6. Keep existing behavior: categories, search, detail route, drafts, my-published, pinned articles, role-gated actions.
7. Update `docs/pages_design/blog_page.md`.
8. Run backend tests, Python compile, and frontend build.
9. Commit, push, deploy changed files, rebuild frontend, restart API if backend changed, and smoke test.

## folder structure
|-blog_product_redesign_and_image_integrity_plan.md implementation plan for blog redesign and image integrity

## 代办
- Consider replacing page reloads after article save/delete with local state updates in a later pass.
