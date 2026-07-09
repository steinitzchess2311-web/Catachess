# Study Breadcrumb Overflow Menu Plan
Created at: 2026-07-08 21:21 EDT
Created by: Codex
Last Modified at: 2026-07-08 21:21 EDT
Last Modified by: Codex

## brief intro
- goal: Implement `docs/requirements/study_breadcrumb_overflow_menu.md`.
- 架构思路: Add a small React breadcrumb renderer inside `PatchStudyPage` and study-scoped CSS that mirrors workspace overflow behavior without changing workspace code.

## plan
- Add constants for visible count, trailing count, and label truncation.
- Replace fixed-depth breadcrumb resolution with visited-node cycle detection.
- Add a `StudyBreadcrumb` component that computes visible, hidden, and trailing items.
- Route visible and hidden crumb clicks through the existing `handleBreadcrumbClick` callback.
- Add study-scoped overflow menu styles in `patch/styles/index.css`.
- Update study page design documentation.
- Run TypeScript build and check for residual overflow/scroll selectors.

## folder structure
|-study_breadcrumb_overflow_menu_plan.md implementation plan for study breadcrumb overflow

## 代办
- Add an automated visual regression test once the study page has a stable fixture.
