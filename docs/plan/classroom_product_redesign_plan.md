Created at: 2026-07-08 23:58:19 EDT
Created by: Codex
Last Modified at: 2026-07-09 00:20:00 EDT
Last Modified by: Codex

# Classroom Product Redesign Plan

## Requirement Source
This plan implements `docs/requirements/classroom_product_redesign.md`.

## Execution Plan
1. Document the product critique and redesign requirements.
2. Add README files for the classroom module and touched component folders.
3. Replace the classroom design tokens and CSS primitives with a restrained blue/white product system.
4. Rework the classroom list header, cards, empty state, and inline join control to remove marketing/decorative treatment.
5. Rework classroom detail shell actions, tabs, menu, toast, and destructive confirmations into product-grade surfaces.
6. Rework core modal-related components that currently carry inline card styling or native alert/confirm behavior.
7. Run the frontend build and inspect screenshots where the local app can be reached.
8. Mark the classroom todo complete only after validation passes.

## Validation
- `npm run build` from `frontend/web`.
- Browser screenshot check of classroom route if authentication/dev server allows.
- Git diff review for unintended unrelated edits.

## Validation Record
- 2026-07-09 00:20 EDT: `npm run build` passed with the existing classroom dynamic/static import Vite warning and existing large chunk warnings.
- 2026-07-09 00:20 EDT: Playwright screenshot self-check passed using mocked classroom API data for:
  - `artifacts/classroom-redesign/list.png`
  - `artifacts/classroom-redesign/detail.png`
  - `artifacts/classroom-redesign/create-modal.png`
  - `artifacts/classroom-redesign/confirm-modal.png`
