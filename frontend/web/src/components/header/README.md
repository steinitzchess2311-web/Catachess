## header
Created at: 2026-07-08 18:43:55 EDT
Created by: Codex
Last Modified at: 2026-07-08 22:36 EDT
Last Modified by: Codex

## brief intro
- goal for this folder: Shared global application header for navigation, account access, notifications, and active-game entry.
- 架构思路: Keep behavior in `Header.tsx` and presentation in `Header.css`; size polish should happen in the final product-refresh CSS layer.

## folder structure
|-Header.tsx React component for logo, global navigation, notifications, active-game entry, and account link
|-Header.css header layout, responsive rules, dropdown styling, and final product-refresh visual overrides

## 代办
- Extract inline account role badge styling into CSS when the account area is redesigned.
- Keep active-game polling adaptive and visibility-aware; avoid reintroducing fixed global 5 second polling.
