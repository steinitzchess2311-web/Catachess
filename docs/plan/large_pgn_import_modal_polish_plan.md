## header
Created at: 2026-07-09 02:06 EDT
Created by: Codex
Last Modified at: 2026-07-09 02:06 EDT
Last Modified by: Codex

## brief intro
- goal: Implementation plan for the large PGN import modal polish.
- 架构思路: Infer from `docs/requirements/large_pgn_import_modal_polish.md` and apply a narrow UI-only change.

## plan
- Add scoped body/footer wrappers in `LargePgnImportModal.tsx`.
- Replace inline modal spacing in parsing/importing states with product CSS classes.
- Update shared patch CSS with large PGN modal spacing, progress card, and responsive rules.
- Update study page design notes and folder READMEs for the changed modal surface.
- Build the frontend and screenshot the modal state if practical.
