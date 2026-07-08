# Workspace Sidebar Collapse Plan
Created at: 2026-07-08 18:49:00 EDT
Created by: Codex
Last Modified at: 2026-07-08 18:49:00 EDT
Last Modified by: Codex

## brief intro
- goal: Execute `docs/requirements/workspace_sidebar_collapse.md`.
- 架构思路: Add minimal DOM, bind one stateful toggle, and style the collapsed rail through a container class.

## plan
1. Add a sidebar collapse toggle to the workspace layout template.
2. Extend extracted workspace elements with the toggle button.
3. Add localStorage-backed collapse state initialization in `initWorkspace`.
4. Bind the toggle to update container class, button accessibility labels, and persisted state.
5. Add CSS for expanded header controls and collapsed rail mode.
6. Update `docs/pages_design/workspace_page.md`.
7. Run frontend build and perform a screenshot check.

## folder structure
|-workspace_sidebar_collapse_plan.md execution plan for workspace sidebar collapse

## 代办
- Add automated visual regression around expanded/collapsed workspace states.
