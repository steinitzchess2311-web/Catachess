## header
Created at: 2026-07-08 16:54:53 EDT
Created by: Codex
Last Modified at: 2026-07-08 16:54:53 EDT
Lst Modified by: Codex

## brief intro
- goal for this file: Define the requested move tree context menu dismissal behavior.
- 架构思路: Keep existing move tree actions intact while making the transient menu close on ordinary outside interaction.

## requirements
- Right-clicking a move may open the context menu.
- Clicking or tapping outside the context menu must close it.
- Pressing Escape while the context menu is open should close it.
- Clicking inside the menu must not close it before the selected action runs.
- Do not change move selection, delete, or promote behavior.
