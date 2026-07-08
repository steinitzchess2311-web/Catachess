# Workspace Sidebar Collapse Grill
Created at: 2026-07-08 18:49:00 EDT
Created by: Codex
Last Modified at: 2026-07-08 18:49:00 EDT
Last Modified by: Codex

## topic workspace left sidebar collapse

## questions
- Should collapse remove the sidebar entirely?
  - No. A full hide creates a recovery problem. Keep a narrow rail with a visible expand control and mode icons.
- What state should persist?
  - Persist only the collapsed/expanded preference in localStorage. Do not persist mode or folder state in this change.
- Should mobile use the collapsed rail?
  - No. The mobile layout already stacks the sidebar above content; forcing a rail would make navigation worse.
- What functionality must remain reachable when collapsed?
  - Workspace mode switching and the expand control. Search and folder tree can hide until expanded because they require text space.
- Should this change alter backend/API behavior?
  - No. It is a front-end layout and interaction change only.
