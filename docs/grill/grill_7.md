## header
Created at: 2026-07-08 16:54:53 EDT
Created by: Codex
Last Modified at: 2026-07-08 16:54:53 EDT
Lst Modified by: Codex

## topic move tree context menu dismissal

1. What is the reported bug?
The move tree context menu remains visible after right-clicking a move and then clicking elsewhere.

2. What should dismiss the menu?
Any pointer interaction outside the context menu, plus Escape, should close it.

3. What must not break?
Clicking the context menu actions must still promote or delete the selected branch before closing the menu.

4. What is the smallest safe fix?
Register a temporary document-level listener only while the menu is open, and stop propagation on the menu itself.
