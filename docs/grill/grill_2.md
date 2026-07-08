# Blog Image Database Write Grill
Created at: 2026-07-08 12:52:00 EDT
Created by: Codex
Last Modified at: 2026-07-08 19:06:00 EDT
Last Modified by: Codex

## topic blog image metadata write correctness

## questions
- Is the image binary expected to live in PostgreSQL?
  - No. Existing architecture uploads the file to Cloudflare R2 and stores metadata, URL, dimensions, and article associations in PostgreSQL.
- What production symptom is confirmed?
  - Cover images are linked as `cover` in `blog_article_images`, but their `blog_images.image_type` values are stored as `content`. Some image URLs also contain raw spaces or Unicode spacing characters from filenames.
- What code path causes the mismatch?
  - The BlogEditor cover image upload calls `blogApi.uploadImage(file)` without sending `image_type=cover`, so the backend default `content` is persisted.
- Can existing production data be repaired safely?
  - Yes. Current production rows have no mixed cover/content image reuse, so cover-only linked images can be updated to `image_type='cover'`.
- What should be tested?
  - TypeScript build for the frontend API/editor call, backend import/compile, CDN URL percent-encoding, R2 image access, and production SQL counts before and after the metadata repair.
- What still looked wrong after the first metadata repair?
  - Production `blog_article_images` rows were correct, but `blog_images.article_id` was still NULL for linked images. That legacy field is not canonical anymore, but leaving it empty makes database admin views and cleanup diagnostics look as if linked images were not stored against articles.
- Should `blog_images.article_id` become the source of truth again?
  - No. Keep `blog_article_images` as the source of truth because it supports multiple image usages and contexts. Maintain `blog_images.article_id` only as a backward-compatible primary-reference/diagnostic field.
