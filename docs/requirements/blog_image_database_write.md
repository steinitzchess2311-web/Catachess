# Blog Image Database Write Requirements
Created at: 2026-07-08 12:52:00 EDT
Created by: Codex
Last Modified at: 2026-07-08 19:06:00 EDT
Last Modified by: Codex

## brief intro
- goal: Ensure blog image uploads persist correct database metadata and article associations.
- 架构思路: Keep image binaries in R2, store durable metadata and relation records in PostgreSQL, and preserve the existing `/api/blogs/upload-image` workflow.

## requirements
- Cover image uploads from BlogEditor must write `blog_images.image_type='cover'`.
- Content image uploads must continue to write `blog_images.image_type='content'`.
- Existing uploaded cover images in production must be corrected without deleting files or changing article URLs.
- Blog image URLs stored in the database must be valid browser-safe URLs, with unsafe filename characters percent-encoded while preserving the R2 object key.
- The backend upload response should expose enough metadata to verify database writes from the client or logs.
- Article image synchronization must keep the canonical `blog_article_images` relation and the legacy `blog_images.article_id` diagnostic field consistent.
- Linked cover/content images must not remain visually orphaned in `blog_images` when viewed through database admin tools.
- The change must not alter authentication, article creation, R2 bucket selection, or existing public article rendering.

## folder structure
|-blog_image_database_write.md requirements for correcting blog image metadata persistence

## 代办
- Add richer content-image insertion support only if the editor workflow later needs inline image upload.
