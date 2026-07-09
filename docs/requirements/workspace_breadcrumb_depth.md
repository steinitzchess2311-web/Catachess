# Workspace Breadcrumb Depth Requirements

## header
Created at: 2026-07-08 20:32 EDT
Created by: Codex
Last Modified at: 2026-07-08 20:32 EDT
Last Modified by: Codex

## brief intro
- goal: Keep workspace breadcrumbs usable when folder nesting and folder-name length are unbounded.
- 架构思路: Limit the visible breadcrumb surface without limiting the underlying folder tree depth.

## folder structure
|-workspace_breadcrumb_depth.md requirements for deep workspace breadcrumb behavior

## Requirements
- Workspace folder nesting must remain unrestricted by the frontend breadcrumb UI.
- Initial breadcrumb reconstruction must not impose a fixed depth cap.
- The breadcrumb must not push the workspace header wider than its container.
- Long folder names must be truncated visually while preserving the full title in native hover text.
- Deep paths must default to a compressed middle state.
- Hidden ancestors must remain reachable through an explicit expand action.
- Expanded deep paths must be horizontally scrollable instead of wrapping into a tall header.
- Root, immediate parent, and current folder context should remain visible in the compressed state.
- Parent-chain traversal must still stop if malformed data creates a cycle.

## Non-Requirements
- Do not change backend folder depth behavior.
- Do not add a modal solely for path navigation.
- Do not restore the removed editable path input.

## 代办
- Consider adding keyboard arrow navigation across breadcrumbs if breadcrumb interactions become central to power-user flows.
