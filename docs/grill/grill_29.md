# Grill 29
Created at: 2026-07-09 01:05 EDT
Created by: Codex
Last Modified at: 2026-07-09 01:05 EDT
Last Modified by: Codex

## topic blog product redesign and image persistence

1. Is this just visual polish?
Recommended answer: No. The user explicitly called out both the blog listing/editor design and the database image issue, so the implementation must cover UI quality and image-link persistence.

2. Should blog images be stored as binary blobs in the database?
Recommended answer: No. Keep binaries in R2 and store metadata plus article-image associations in PostgreSQL. The phrase "数据库存图片" should be implemented as durable DB metadata and relationships, not raw image bytes.

3. What is the minimum product-level UI change?
Recommended answer: Remove toy-like inline styling, use a restrained blue/white editorial layout, make article cards denser and cleaner, and redesign the create/edit modal as a serious writing surface.

4. How do we prevent image database drift?
Recommended answer: Article create/update should save article and image associations in one transaction. If image sync fails, rollback the article mutation instead of silently leaving images orphaned.

5. What must be verified?
Recommended answer: Backend compile, focused image-linker tests, frontend build, and a production deploy smoke check after restart.
