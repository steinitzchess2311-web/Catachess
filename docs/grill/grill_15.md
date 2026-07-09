# Workspace Breadcrumb Depth Grill

## header
Created at: 2026-07-08 20:32 EDT
Created by: Codex
Last Modified at: 2026-07-08 20:32 EDT
Last Modified by: Codex

## topic workspace breadcrumb depth

### 1. What breaks when nesting is unlimited?
The workspace breadcrumb can render every ancestor in one row. Deep folders and long names compete with the page title and actions, making the header unreadable.

Recommended answer: keep unlimited folder depth in data, but cap the visible breadcrumb surface.

### 2. Is character limiting enough?
No. Per-item truncation protects long folder names, but many short folder names can still overflow.

Recommended answer: combine label truncation with middle compression.

### 3. Should the whole breadcrumb always scroll?
Not by default. A permanently scrollable path hides important context and feels unfinished on desktop.

Recommended answer: show a compressed path by default, then allow the user to expand to a horizontally scrollable full path when needed.

### 4. What context should remain visible?
Users need the workspace root, immediate parent context, and current folder most of the time.

Recommended answer: for deep paths, render `Root / ... / Parent / Current`, with `...` expanding the full path.
