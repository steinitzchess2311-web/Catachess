# Workspace Sidebar Collapse Requirements
Created at: 2026-07-08 18:49:00 EDT
Created by: Codex
Last Modified at: 2026-07-08 18:49:00 EDT
Last Modified by: Codex

## brief intro
- goal: Add a product-grade collapsible left sidebar to the workspace browser.
- 架构思路: Preserve the existing static template/event architecture and add a small UI state class on the workspace container.

## requirements
- Users must be able to collapse and expand the workspace left sidebar from a visible control.
- Collapsed desktop state must leave a narrow rail so users can recover without hunting.
- Mode switching must remain available in collapsed state.
- Search and folder tree may hide in collapsed state.
- Collapsed/expanded preference must persist in localStorage.
- Mobile layout must remain compact and not use the desktop rail.
- The change must not alter node APIs, routing, drag/drop, create actions, search semantics, or study opening behavior.
- The frontend build must pass.

## folder structure
|-workspace_sidebar_collapse.md requirements for workspace sidebar collapse behavior

## 代办
- Consider keyboard shortcut support after the workspace shell is fully redesigned.
