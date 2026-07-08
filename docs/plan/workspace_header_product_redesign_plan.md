# Workspace Header Product Redesign Plan

## Header
Created at: 2026-07-08 18:02 EDT
Created by: Codex
Last Modified at: 2026-07-08 18:02 EDT
Last Modified by: Codex

## Requirement Reference
- `docs/requirements/workspace_header_product_redesign.md`

## Plan
- Update `frontend/ui/modules/workspace/layout/index.html`:
  - remove the visible path jump block from the header.
  - add a `workspace-header-actions` region with Create folder, Create study, and sort controls.
- Update `frontend/ui/modules/workspace/events/types.ts` and `initialization.ts` so `pathInput` is optional.
- Update `eventHandlers.ts` to bind create action buttons and skip path handlers when no path input exists.
- Update `rendering.ts` so create actions are visible only in private mode.
- Update `frontend/ui/modules/workspace/styles/index.css` for the compact header, action buttons, breadcrumb, and responsive layout.
- Update `SortToggles` component styles to read as a quiet segmented sort control.
- Add missing README files for touched workspace folders.
- Build the frontend and run a local screenshot check if the app can start.
