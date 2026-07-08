# Workspace Study Modal Product Redesign Plan

## header
Created at: 2026-07-08 20:05 EDT
Created by: Codex
Last Modified at: 2026-07-08 20:05 EDT
Last Modified by: Codex

## brief intro
- goal: Execution plan for `docs/requirements/workspace_study_modal_product_redesign.md`.
- 架构思路: Add a small shared workspace dialog style layer, refactor dialog markup to use it, align the analysis study picker CSS, then verify build and screenshots.

## folder structure
|-workspace_study_modal_product_redesign_plan.md plan for workspace/study modal redesign

## Plan
1. Read current dialog components and analysis picker to identify duplicated modal chrome.
2. Add a shared dialog CSS file in `frontend/web/src/components/dialogBox`.
3. Refactor workspace node dialogs to use shared modal classes while preserving API behavior.
4. Replace emoji with consistent inline icons and action labels.
5. Restyle `StudyPickerModal` through `analysis.css` to match the workspace modal language.
6. Update `docs/pages_design` with modal design rules.
7. Run frontend build.
8. Start a local dev server and capture screenshots for the workspace share modal and analysis study picker.
9. Commit only the redesign and documentation files.

## 代办
- If screenshots reveal layout defects, iterate before committing.
