# Global Header Size Tuning Requirements
Created at: 2026-07-08 18:43:55 EDT
Created by: Codex
Last Modified at: 2026-07-08 18:43:55 EDT
Last Modified by: Codex

## brief intro
- goal: Make the global header slightly taller and scale text/logo/actions in the same visual rhythm.
- 架构思路: Keep the existing header component and route behavior; tune only the final product-refresh CSS layer that controls the visible layout.

## requirements
- Desktop header height must increase slightly from the current visible 76px.
- Logo height, primary navigation text, account label, and icon buttons must scale with the header.
- Mobile header must remain compact and avoid consuming extra vertical viewport space.
- No navigation routes, auth behavior, notification logic, or game-challenge logic should change.
- The result must build with the existing frontend build command.

## folder structure
|-global_header_size_tuning.md requirements for global header sizing polish

## 代办
- Revisit responsive navigation if more top-level links are added.
