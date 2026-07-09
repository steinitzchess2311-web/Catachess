Created at: 2026-07-08 23:58:19 EDT
Created by: Codex
Last Modified at: 2026-07-08 23:58:19 EDT
Last Modified by: Codex

# Classroom Product Redesign Requirements

## Scope
Redesign the classroom frontend pages and core modal surfaces so they match the product-grade workspace and study interface direction.

## Functional Requirements
- Preserve all existing classroom actions and API behavior.
- Preserve classroom list grouping by teaching and enrolled.
- Preserve classroom detail tabs: overview, assignments, members.
- Preserve create classroom, join classroom, broadcast, add member, invite code, contact teacher, share workspace, rename, archive, delete, and leave flows.
- Replace primary native browser confirmation and alert flows in the classroom shell with in-app product dialogs or inline error states.
- Keep classroom controls readable on desktop and mobile.

## Visual Requirements
- Use blue/white as the dominant palette with slate text and restrained status colors.
- Match workspace and study surface language: compact headers, clean borders, limited shadows, no decorative gradients, no toy-like colorful cards.
- Use cards only for repeated data items, modals, and framed tools.
- Keep border radius at or below 8px unless an existing local control requires otherwise.
- Use segmented tabs, compact buttons, and simple menu surfaces.
- Avoid visible product-explainer copy when a control label already communicates the action.

## Non-Functional Requirements
- The redesign must remain compatible with the existing Vite/React build.
- CSS should be centralized in `classroom.css` where practical instead of expanding inline styling.
- The code should remain narrow to classroom frontend files.
- Documentation and README coverage must be updated for touched folders.
