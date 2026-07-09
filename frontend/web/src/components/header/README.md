## header
Created at: 2026-07-08 18:43:55 EDT
Created by: Codex
Last Modified at: 2026-07-09 02:27 EDT
Last Modified by: Codex

## brief intro
- goal for this folder: Shared global application header for navigation, account access, unified notifications, and active-game entry.
- 架构思路: Keep behavior in `Header.tsx` and presentation in `Header.css`; CataChat and workspace notifications are aggregated here while keeping existing service APIs separate.

## folder structure
|-Header.tsx React component for logo, global navigation, CataChat/workspace notifications, active-game entry, and account link
|-Header.css header layout, responsive rules, notification dropdown styling, and final product-refresh visual overrides

## 代办
- Move CataChat seen state to server-side read state when the CataChat API supports it.
- Keep active-game polling adaptive and visibility-aware; avoid reintroducing fixed global 5 second polling.
