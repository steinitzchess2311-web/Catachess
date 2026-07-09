# Workspace Breadcrumb Depth Plan

## header
Created at: 2026-07-08 20:32 EDT
Created by: Codex
Last Modified at: 2026-07-08 20:32 EDT
Last Modified by: Codex

## brief intro
- goal: Execution plan for `docs/requirements/workspace_breadcrumb_depth.md`.
- 架构思路: Update breadcrumb rendering first, then constrain layout with CSS and verify the production build.

## folder structure
|-workspace_breadcrumb_depth_plan.md plan for deep breadcrumb handling

## Plan
1. Update workspace breadcrumb rendering to compress middle ancestors after a small visible threshold.
2. Add an overflow button that expands the full path for navigation.
3. Truncate breadcrumb labels by character count while keeping full titles in `title`.
4. Make the breadcrumb rail horizontally scrollable in expanded and fallback states.
5. Remove the fixed parent traversal depth cap while keeping parent-cycle protection.
6. Update workspace design documentation and event-module README notes.
7. Run the frontend production build.
8. Commit and deploy the change.

## 代办
- Capture a browser screenshot after deployment if authenticated workspace data is available.
