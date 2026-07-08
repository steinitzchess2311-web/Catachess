## header
Created at: 2026-07-08 16:10:00 EDT
Created by: Codex
Last Modified at: 2026-07-08 16:10:00 EDT
Lst Modified by: Codex

## brief intro
- goal for this file: Implementation plan for the engine analysis panel cleanup.
- 架构思路: Update the shared analysis panel component and its shared patch sidebar styles, then verify with a production frontend build.

## related requirement
- docs/requirements/engine_analysis_plain_ui.md

## plan
1. Remove the status/health/source/time row from `AnalysisPanel`.
2. Change empty-state rendering to depend on `lines.length === 0`.
3. Replace the decorative analysis panel styles with plain bordered white sections.
4. Run the frontend production build.

## 代办
- Capture a browser screenshot after deployment if authenticated study data is available.
