# Workspace Breadcrumb Overflow Menu Grill

## header
Created at: 2026-07-08 20:48 EDT
Created by: Codex
Last Modified at: 2026-07-08 20:48 EDT
Last Modified by: Codex

## topic workspace breadcrumb overflow menu

### 1. Why did the previous scroll behavior fail?
The expanded breadcrumb used a native horizontal scrollbar. It technically preserved every path segment, but it made the visible path look shifted and unclear.

Recommended answer: remove the horizontal-scroll interaction from the default workspace header.

### 2. What should `...` mean?
`...` should be an overflow control for hidden ancestor folders, not a command that turns the whole breadcrumb into a scroll rail.

Recommended answer: open a compact menu listing hidden ancestors; clicking an ancestor navigates there.

### 3. How should very long visible names behave?
Visible crumb labels should remain truncated with ellipsis and full native hover text. This keeps the header stable.

Recommended answer: preserve character and width truncation for root, parent, and current crumbs.
