## header
Created at: 2026-07-08 16:10:00 EDT
Created by: Codex
Last Modified at: 2026-07-08 16:10:00 EDT
Lst Modified by: Codex

## brief intro
- goal for this file: Define the requested simplification of the engine analysis sidebar.
- 架构思路: Keep engine controls and PV output intact while reducing decorative presentation and fixing empty-state logic.

## requirements
- Remove the small status labels for ready/running state, engine health, engine origin, and last update time.
- Do not show "No analysis yet" when one or more analysis lines are present.
- Keep depth, line count, engine toggle, score, and PV lines available.
- Make the panel visually plain: white background, thin borders, restrained typography, no gradient hero, no large dark score tile.

## 代办
- Consider adding a small deterministic UI test for the empty-state condition.
