# Workspace Page Design

## Header
Created at: 2026-07-08 18:02 EDT
Created by: Codex
Last Modified at: 2026-07-08 18:49 EDT
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
- Keep create actions primary in private mode.
- Keep sorting secondary and visually grouped.
- Keep the header short; avoid large empty horizontal bands.
- Sidebar collapse is a local UI preference and must not change active workspace mode or folder.

## Visual Direction
- Product UI, blue and white, quiet density.
- No decorative gradients, oversized hero treatment, or duplicate labels.
- Icons are acceptable inside controls when they clarify the command.
