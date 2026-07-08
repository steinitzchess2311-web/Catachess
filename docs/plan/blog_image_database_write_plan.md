# Blog Image Database Write Plan
Created at: 2026-07-08 12:52:00 EDT
Created by: Codex
Last Modified at: 2026-07-08 19:06:00 EDT
Last Modified by: Codex

## brief intro
- goal: Execute the requirements in `docs/requirements/blog_image_database_write.md`.
- 架构思路: Fix the narrow upload metadata contract first, repair existing production rows with a constrained SQL update, then verify counts and deployment health.

## plan
1. Confirm current production image metadata and R2 configuration.
2. Update the frontend API client to send explicit image upload intent.
3. Update BlogEditor cover upload to pass `image_type=cover`.
4. Keep backend defaults compatible while returning `image_type` and `id` for diagnostics.
5. Generate future CDN URLs with percent-encoded R2 paths.
6. Run frontend build and backend compile checks.
7. Deploy changed files to the server, restart the API service if backend changed.
8. Update production `blog_images.image_type` for cover-only linked images.
9. Normalize existing `blog_images.url`, article cover URLs, and content references to encoded URLs.
10. Re-query mismatch counts, health endpoints, and sample R2 image access.
11. Keep `blog_images.article_id` in sync as a legacy primary-reference field when `blog_article_images` links are created or removed.
12. Backfill production `blog_images.article_id` from existing `blog_article_images` rows.

## folder structure
|-blog_image_database_write_plan.md execution plan for correcting blog image database writes

## 代办
- Add automated regression tests for `blogApi.uploadImage` once the frontend test harness is standardized.
