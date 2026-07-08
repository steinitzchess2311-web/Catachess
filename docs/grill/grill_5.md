## header
Created at: 2026-07-08 16:10:00 EDT
Created by: Codex
Last Modified at: 2026-07-08 16:10:00 EDT
Lst Modified by: Codex

## topic engine analysis panel simplification

1. What is visually wrong?
The analysis panel uses a gradient hero, a large dark score tile, uppercase labels, and multiple status pills. This makes a utilitarian engine panel feel noisy.

2. Which labels should be removed?
The runtime status pill, health pill, engine-origin pill, and timestamp pill should not render in the analysis panel.

3. Why can "No analysis yet" and a line appear together?
The empty state is controlled by `engineEnabled`, not by whether analysis lines exist. If the engine is turned off after lines were produced, the empty state and previous lines can render together.

4. What is the minimum safe fix?
Show the empty state only when `lines.length === 0`, and preserve existing lines without adding status noise.
