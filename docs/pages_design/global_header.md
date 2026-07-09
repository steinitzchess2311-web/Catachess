# Global Header
Created at: 2026-07-08 18:43:55 EDT
Created by: Codex
Last Modified at: 2026-07-09 02:42 EDT
Last Modified by: Codex

## brief intro
- goal: Document the shared product header used across CataChess pages.
- 架构思路: A restrained white application bar with a prominent logo, primary navigation, and compact account/action controls.

## layout
- Desktop: 84px sticky header, logo on the left, navigation immediately beside it, notification/game/account controls on the right.
- Tablet/mobile: compact wrapping header with the logo reduced; very narrow screens move primary navigation to its own row so top-level links remain visible.
- Visual tone: white surface, quiet gray labels, green accent on hover/primary actions.
- Notification menu: one compact list for messages, broadcasts, and workspace study/share invites. Workspace notifications navigate inside CataChess; CataChat items bridge to the chat route with the existing JWT.

## folder structure
|-global_header.md product layout notes for the shared header

## 代办
- Define a dedicated mobile navigation pattern if top-level sections grow beyond the current set.
