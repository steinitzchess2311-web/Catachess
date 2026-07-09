# Patch Styles

## header
Created at: 2026-07-08 20:24 EDT
Created by: Codex
Last Modified at: 2026-07-09 02:06 EDT
Last Modified by: Codex

## brief intro
- goal for this folder: Global CSS for patch study, analysis, and related chess workbench modules.
- 架构思路: Keep shared patch layout and modal primitives in `index.css`; module-specific CSS should stay in module folders unless the selector is intentionally shared across the study workbench.

## folder structure
|-index.css shared patch study styles, modal primitives, large PGN import progress states, board layout, sidebars, and study workflow surfaces
|-README.md folder documentation

## 代办
- Continue extracting heavily scoped module styles into each module folder when a component is no longer shared.
