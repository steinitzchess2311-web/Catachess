## header
Created at: 2026-07-08 23:20 EDT
Created by: Codex
Last Modified at: 2026-07-08 23:20 EDT
Lst Modified by: Codex

## brief intro
- goal for this file: Execution plan inferred from `docs/requirements/predictor_maia_catie.md`.
- 架构思路: First add backend provider adapters with deterministic tests, then replace the hidden imitator frontend with a focused Predictor panel.

## plan
1. Add predictor configuration for Maia2 script, Python path, model type, Catie base URL, concurrency, and timeouts.
2. Add backend predictor service with unified request/response schemas.
3. Implement Maia provider via bounded subprocess and parse its JSON top moves.
4. Implement Catie provider via `/api/model/probe-position` create/poll calls and convert policy top-k to predictor rows.
5. Add `backend/routers/predictor.py` and mount it under `/api/predictor`.
6. Replace frontend `useImitator` with `usePredictor` while keeping compatibility of component filenames where practical.
7. Update Study sidebar and Analysis page sidebars to show Predictor tabs.
8. Verify backend unit tests, py_compile, frontend build, remote smoke, and deploy.

## 代办
- Add client-side cancellation if users scrub through positions quickly during predictor requests.
