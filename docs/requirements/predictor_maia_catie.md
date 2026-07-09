## header
Created at: 2026-07-08 23:20 EDT
Created by: Codex
Last Modified at: 2026-07-08 23:20 EDT
Lst Modified by: Codex

## brief intro
- goal for this file: Define requirements for Maia and Catie human move predictors in study and analysis pages.
- 架构思路: Use CataChess backend as the only frontend API surface; backend fans out to local Maia2 subprocess or CatieChess local model API with bounded concurrency.

## requirements
- Add a Predictor tab next to Chapters and Analysis in the study sidebar.
- Add an Analysis/Predictor horizontal tab group on the analysis page left sidebar.
- Provide exactly two predictor providers in this pass: Maia and Catie.
- Predictor results must show human move probabilities and move choices, not engine evaluation.
- Maia must use the existing server Maia2 model and weights when available.
- Maia inference must be bounded by server-wide concurrency and timeout controls.
- Catie must call the existing CatieChess model API from the backend, not from the browser.
- Catie requests must poll queued tasks with a timeout and return a controlled error if the worker is unavailable.
- The frontend must keep the UI compact and product-grade, matching the current study/analysis sidebars.
- Old coach/player/engine imitator controls should not be shown for this predictor pass.

## 代办
- Add multiple Maia model type choices if blitz/rapid selection becomes product-critical.
