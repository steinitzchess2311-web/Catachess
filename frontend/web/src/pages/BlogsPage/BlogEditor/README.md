## header
Created at: 2026-07-08 12:52:00 EDT
Created by: Codex
Last Modified at: 2026-07-09 01:42 EDT
Last Modified by: Codex

## brief intro
- goal for this folder: Compose the blog article create/edit dialog, including metadata fields, cover image upload, and rich text editing.
- 架构思路: Keep the dialog shell in `index.tsx` and split reusable controls into small local components with explicit props.

## folder structure
|-CategorySelect.tsx category and author type selectors
|-ExitConfirmDialog.tsx unsaved-change confirmation actions
|-ImageUpload.tsx cover image file input and preview
|-RichTextEditor.tsx TipTap editor with Markdown serialization
|-index.tsx BlogEditor state, upload, and save orchestration

## 代办
- Add inline content image insertion if authors need images inside the article body.
