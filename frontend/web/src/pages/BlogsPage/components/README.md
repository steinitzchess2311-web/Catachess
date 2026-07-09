## header
Created at: 2026-07-09 01:42 EDT
Created by: Codex
Last Modified at: 2026-07-09 01:42 EDT
Last Modified by: Codex

## brief intro
- goal for this folder: Shared presentational states and article body rendering for the blog page.
- 架构思路: Keep loading, empty, error, pagination, and Markdown rendering components stateless so route-level data logic stays in `ContentArea.tsx`.

## folder structure
|-EmptyState.tsx empty results state
|-ErrorState.tsx API failure state
|-LoadingState.tsx loading state
|-MarkdownRenderer.tsx GitHub-flavored Markdown renderer
|-Pagination.tsx list pagination controls

## 代办
- Add keyboard-focused pagination tests if blog page UI tests are introduced.
