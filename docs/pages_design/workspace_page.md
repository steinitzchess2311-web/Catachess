# Workspace Page Design

## Header
Created at: 2026-07-08 18:02 EDT
Created by: Codex
Last Modified at: 2026-07-08 20:33 EDT
Last Modified by: Codex

## Page Job
- Let a chess user browse folders and studies, create new material, and open existing material with minimal navigation ambiguity.

## Layout
- Left sidebar owns workspace modes, search, and folder tree.
- Desktop left sidebar can collapse into a 64px recovery rail with mode icons and an expand control.
- Main header owns the current workspace title, breadcrumb location, create actions, and sort.
- Main content grid owns folders, studies, and optional create cards.

## Header Rules
- Do not expose an editable filesystem-like path field in the main header.
- Use breadcrumb as the only visible current-location control.
- Deep breadcrumbs compress the middle ancestors by default and can expand into a horizontal scroll rail.
- Breadcrumb labels truncate visually; the full folder name remains available through native hover text.
- Folder depth is not limited by the breadcrumb UI; malformed parent cycles stop breadcrumb reconstruction.
- Keep create actions primary in private mode.
- Keep sorting secondary and visually grouped.
- Keep the header short; avoid large empty horizontal bands.
- Sidebar collapse is a local UI preference and must not change active workspace mode or folder.

## Visual Direction
- Product UI, blue and white, quiet density.
- No decorative gradients, oversized hero treatment, or duplicate labels.
- Icons are acceptable inside controls when they clarify the command.

## Dialog Rules
- Workspace dialogs use the shared `cc-dialog-*` primitives.
- Dialog cards use compact radius, white surfaces, slate text, and blue primary actions.
- Emoji must not be used as primary interface icons.
- Each dialog header names the job, not the internal object type twice.
- Node action menus show metadata plainly; do not hide important details behind hover-only tooltips.
- Node action headers show type and title only; created/updated dates belong in the body metadata block.
- Destructive actions use red only for the destructive control and supporting warning state.
- Share settings use three visibility choices: Public, Private, Shared.
