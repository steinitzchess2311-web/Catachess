## header
Created at: 2026-07-08 17:25:00 EDT
Created by: Codex
Last Modified at: 2026-07-08 17:25:00 EDT
Lst Modified by: Codex

## brief intro
- goal for this file: Implementation plan for removing engine line labels.
- 架构思路: Touch only the shared analysis panel component and the affected row-head alignment style.

## related requirement
- docs/requirements/engine_analysis_line_labels.md

## plan
1. Remove the row label span from `AnalysisPanel`.
2. Align the row header score to the right.
3. Run the frontend production build.
