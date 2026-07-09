# Blog Page Design
Created at: 2026-07-09 01:05 EDT
Created by: Codex
Last Modified at: 2026-07-09 01:05 EDT
Last Modified by: Codex

## brief intro
- goal: Document the blog list/detail/editor layout so future changes preserve a product-grade CataChess surface.
- 架构思路: Blog uses the same quiet blue/white product language as workspace/study, with a utility sidebar and a focused writing modal.

## layout
- `/blogs` renders a two-column product layout: a sticky category rail on the left and a content column on the right.
- The content column contains `BlogHeader` followed by `ContentArea`.
- List mode shows a flat article grid, not nested cards inside decorative cards.
- Detail mode keeps the same shell but collapses the sidebar rail for reading focus.
- Editor mode uses a centered modal with a fixed header, scrollable body, and sticky footer actions.

## visual system
- Palette: white surface, near-white app background, slate text, blue action/accent, restrained gray borders.
- Cards use 8px radius, clear borders, and minimal shadow.
- Controls use sentence-case action labels and familiar icons where existing icon imports are available.
- No decorative gradient blobs, oversized badges, or playful color mixing.

## behavior
- Search and category filters remain URL-driven.
- Editor/admin users can create and manage articles according to existing role checks.
- Uploaded images are stored in R2, while `blog_images` and `blog_article_images` keep database metadata and article relations.

## folder structure
|-blog_page.md design document for blog list/detail/editor pages

## 代办
- Add screenshot references after the next Playwright visual pass.
