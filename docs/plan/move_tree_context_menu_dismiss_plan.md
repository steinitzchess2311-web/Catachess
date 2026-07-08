## header
Created at: 2026-07-08 16:54:53 EDT
Created by: Codex
Last Modified at: 2026-07-08 16:54:53 EDT
Lst Modified by: Codex

## brief intro
- goal for this file: Implementation plan for the move tree context menu dismissal fix.
- 架构思路: Add scoped event listeners in the shared move tree display component and verify with the production frontend build.

## related requirement
- docs/requirements/move_tree_context_menu_dismiss.md

## plan
1. Add a menu ref and document-level pointer/keyboard listeners while the menu is open.
2. Ignore pointer events that originate inside the menu.
3. Stop propagation on the menu container.
4. Run the frontend production build.
