## header
Created at: 2026-07-08 23:05 EDT
Created by: Codex
Last Modified at: 2026-07-08 23:05 EDT
Lst Modified by: Codex

## brief intro
- goal for this folder: Presentation components for study/game sidebars.
- 架构思路: Keep components stateless and reusable; hooks own network and engine lifecycle logic.

## folder structure
|-README.md intro to this folder
|-AnalysisPanel.tsx renders engine scores and PV lines
|-AnalysisSettings.tsx renders depth, MultiPV, engine selector, and engine enable toggle
|-ImitatorPanel.tsx renders predictor/imitator move results
|-ImitatorSettings.tsx renders predictor/imitator target controls

## 代办
- Add lightweight component tests for empty-state rendering.
