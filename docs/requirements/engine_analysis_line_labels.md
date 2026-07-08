## header
Created at: 2026-07-08 17:25:00 EDT
Created by: Codex
Last Modified at: 2026-07-08 17:25:00 EDT
Lst Modified by: Codex

## brief intro
- goal for this file: Define the requested removal of engine variation text labels.
- 架构思路: Keep the existing analysis data and layout structure while removing redundant row labels.

## requirements
- Remove the visible "Best line" label from the first engine analysis row.
- Remove the visible "Candidate" label from non-primary engine analysis rows.
- Preserve row numbering, score coloring, and PV move text.
- Avoid changing engine behavior or analysis state handling.
