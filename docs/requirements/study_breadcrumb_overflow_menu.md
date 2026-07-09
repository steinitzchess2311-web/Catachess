# Study Breadcrumb Overflow Menu Requirements
Created at: 2026-07-08 21:21 EDT
Created by: Codex
Last Modified at: 2026-07-08 21:21 EDT
Last Modified by: Codex

## brief intro
- goal: Prevent long study breadcrumbs from overflowing the study header.
- 架构思路: Match the workspace breadcrumb interaction: truncate labels, compress middle ancestors, and expose hidden ancestors through an overflow menu.

## requirements
- Study page breadcrumbs must not horizontally scroll across the header.
- Long study paths must compress middle ancestors into a `...` overflow control.
- The first breadcrumb item and last two breadcrumb items should remain visible when compression is active.
- Hidden ancestors must be reachable through a menu opened from `...`.
- Clicking a hidden ancestor must preserve the existing unsaved-change warning behavior.
- Breadcrumb label text must truncate visually and expose the full title through `title`.
- Breadcrumb path resolution must not impose an arbitrary maximum folder depth.
- Breadcrumb path resolution must still stop on malformed parent cycles.

## folder structure
|-study_breadcrumb_overflow_menu.md requirements for study page breadcrumb overflow

## 代办
- Consider extracting a shared React breadcrumb primitive after workspace fully migrates from DOM rendering.
