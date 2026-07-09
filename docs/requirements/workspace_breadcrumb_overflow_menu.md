# Workspace Breadcrumb Overflow Menu Requirements

## header
Created at: 2026-07-08 20:48 EDT
Created by: Codex
Last Modified at: 2026-07-08 20:48 EDT
Last Modified by: Codex

## brief intro
- goal: Replace the unclear horizontal breadcrumb scrollbar with an explicit hidden-folder menu.
- 架构思路: Keep the breadcrumb compressed and stable, while making hidden ancestors reachable through the `...` control.

## folder structure
|-workspace_breadcrumb_overflow_menu.md requirements for breadcrumb hidden ancestor menu

## Requirements
- The workspace breadcrumb must not show a native horizontal scrollbar as its primary overflow interaction.
- The `...` breadcrumb control must open a menu of hidden ancestor folders.
- Clicking a hidden ancestor in the menu must navigate to that folder.
- Clicking outside the menu or pressing Escape must close it.
- Root, parent, and current crumb labels must remain visible in the compressed breadcrumb.
- Long visible crumb names must still truncate visually and expose the full title through native hover text.

## Non-Requirements
- Do not add a separate path modal.
- Do not reintroduce the editable path input.
- Do not change backend folder depth behavior.

## 代办
- Consider adding keyboard roving focus if the overflow menu grows more complex.
