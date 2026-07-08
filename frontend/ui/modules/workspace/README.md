## header
Created at: 2026-07-08 18:02 EDT
Created by: Codex
Last Modified at: 2026-07-08 18:02 EDT
Last Modified by: Codex

## brief intro
- goal for this folder.
  - Legacy workspace UI module for browsing folders and studies.
  - The page is composed from an HTML template, event modules, and shared CSS.
- 架构思路
  - `layout/` provides static templates.
  - `events/` owns navigation, rendering, state, modals, and handlers.
  - `styles/` owns the workspace visual system.

## folder structure
|-events/ workspace state, handlers, rendering, navigation, and modal orchestration
|-layout/ workspace HTML templates
|-styles/ workspace CSS

## 代办
- Continue reducing duplicated navigation concepts in the legacy workspace UI.
