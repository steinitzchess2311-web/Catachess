# Performance Reports
Created at: 2026-07-08 22:36 EDT
Created by: Codex
Last Modified at: 2026-07-08 22:36 EDT
Last Modified by: Codex

## brief intro
- goal for this folder: Performance test reports, large generated PGN samples, and command output used for import, tagger, and frontend responsiveness analysis.
- 架构思路: Keep measured findings and residual performance risks separate from implementation plans.

## folder structure
|-README.md intro to this folder
|-frontend_jank_reduction.md report for the global frontend jank reduction loop
|-*.txt raw command output or migration/performance attempts
|-*.json structured performance summaries
|-*.md performance reports and rollout notes
|-large_pgn_generated.pgn large fixture for import/tagger performance work

## 代办
- Large generated fixtures here should not be deployed unless they are intentionally needed by tests or docs.
