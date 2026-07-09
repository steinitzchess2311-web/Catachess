## header
Created at: 2026-07-09 01:05 EDT
Created by: Codex
Last Modified at: 2026-07-09 01:42 EDT
Last Modified by: Codex

## brief intro
- goal for this folder.
- Blog listing, article detail, category sidebar, editor, cards, comments, and supporting states.
- 架构思路
- Keep route state in `index.tsx`, data presentation in `ContentArea.tsx`, card composition in `ArticleCard/`, and authoring controls in `BlogEditor/`.

## folder structure
|-index.tsx route-level blog page shell and URL state
|-BlogsPage.css shared product styling for blog list/detail/editor surfaces
|-ContentArea.tsx article list/detail content switch
|-ArticleDetailContent.tsx article reading content
|-ArticleDetailPage.tsx standalone/embedded article detail
|-ArticleModal.tsx legacy modal article presentation
|-CreateButton.tsx legacy create button wrapper
|-UserRoleDebug.tsx role diagnostic helper
|-ArticleCard/ blog card subcomponents
|-BlogEditor/ article create/edit dialog
|-CategorySidebar/ blog category and author actions sidebar
|-Comments/ article comment components
|-components/ shared list states, pagination, and Markdown rendering

## 代办
- Replace remaining `window.location.reload()` refresh paths with local state updates.
