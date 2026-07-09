## header
Created at: 2026-07-09 01:18 EDT
Created by: Codex
Last Modified at: 2026-07-09 01:18 EDT
Last Modified by: Codex

## brief intro
- goal for this folder: Render blog article cards for the listing page with consistent media, metadata, actions, and category controls.
- 架构思路: Keep `ArticleCard.tsx` as the coordinator and split media, text, and metadata rendering into focused components.

## folder structure
|-ArticleCard.tsx clickable card shell and admin actions
|-ArticleContent.tsx title and subtitle presentation
|-ArticleImage.tsx cover image and fallback rendering
|-ArticleMeta.tsx author, category, and date metadata

## 代办
- Replace card-level refreshes after admin actions with optimistic local state updates.
