# Workspace Study Modal Product Redesign Requirements

## header
Created at: 2026-07-08 20:05 EDT
Created by: Codex
Last Modified at: 2026-07-08 20:05 EDT
Last Modified by: Codex

## brief intro
- goal: Define the product requirements for making workspace and study workflow dialogs visually coherent and production-grade.
- 架构思路: Preserve existing behavior while standardizing modal layout, hierarchy, typography, buttons, and icon treatment.

## folder structure
|-workspace_study_modal_product_redesign.md requirements for workspace/study modal redesign

## Requirements
- Workspace node dialogs must use one consistent modal structure: overlay, card, header, content, and footer.
- Workspace dialogs must remove emoji as primary UI icons.
- Share visibility options must remain public, private, and shared with specific people.
- Share user search, add, remove, and owner display must remain functional.
- Create, rename, move, delete, drag-move, restore, and delete-forever actions must remain available.
- Destructive actions must be visually distinguishable without dominating the UI.
- The analysis "Send to Study" picker must visually align with the workspace modal system.
- The redesign must keep existing keyboard close behavior and outside-click close behavior.
- The UI must be responsive on narrow screens without overflowing buttons or modal content.
- Documentation must record the modal design rules under `docs/pages_design`.

## Non-Requirements
- Do not change backend APIs.
- Do not redesign classroom, blog, games, or admin modals in this pass.
- Do not add a new third-party design system.

## 代办
- Later passes can migrate unrelated module modals to the same dialog language.
