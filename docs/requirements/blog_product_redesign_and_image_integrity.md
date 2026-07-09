# Blog Product Redesign And Image Integrity Requirements
Created at: 2026-07-09 01:05 EDT
Created by: Codex
Last Modified at: 2026-07-09 01:05 EDT
Last Modified by: Codex

## brief intro
- goal: Rebuild the blog list/editor experience to match the product quality of workspace/study and make blog image database metadata reliable.
- 架构思路: Preserve the existing API contract and article model while tightening image synchronization and moving frontend blog UI toward a restrained blue/white product surface.

## requirements
- Blog list, sidebar, cards, and editor modal must look like a real product surface, not a toy page.
- The UI should remain compatible with current categories, pinned articles, drafts, my-published articles, article detail, comments, and create/edit flows.
- The page should use restrained blue/white styling, dense spacing, 8px-or-less radii where practical, and no decorative gradient/orb background.
- The editor modal should provide a structured writing workflow with clear metadata, cover, content, and save/publish actions.
- Article cards must be easy to scan and avoid oversized decoration.
- Blog image binaries remain in R2; database stores image metadata and `blog_article_images` associations.
- Article create/update must not silently succeed if image relation synchronization fails.
- Cover URLs and content image URLs must be normalized enough for existing encoded/unencoded URL variants to match database rows.
- The change must not alter authentication rules, role permissions, article publishing semantics, or public article URLs.

## folder structure
|-blog_product_redesign_and_image_integrity.md requirements for blog UI redesign and image metadata integrity

## 代办
- Add richer inline image authoring later if authors need content image upload inside the editor.
