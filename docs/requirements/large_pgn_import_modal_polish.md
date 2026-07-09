## header
Created at: 2026-07-09 02:06 EDT
Created by: Codex
Last Modified at: 2026-07-09 02:06 EDT
Last Modified by: Codex

## brief intro
- goal: Requirements for polishing the large PGN import loading modal.
- 架构思路: Treat the import modal as an operational status dialog with clear spacing, not a generic alert box.

## requirements
- The parsing progress row must have comfortable padding above and below.
- The modal body, progress card, and footer actions must be visually separated with consistent spacing.
- Progress status text must remain readable while a large file is being parsed.
- Import logic, worker parsing, batching, cancellation, and API calls must not change.
- Mobile layout must still fit within the viewport and preserve full-width action buttons.

## non-goals
- Do not redesign the full PGN import workflow.
- Do not change the large PGN parsing worker or batching size.
