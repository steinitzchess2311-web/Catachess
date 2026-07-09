# Frontend Jank Diagnosis Grill
Created at: 2026-07-08 22:36 EDT
Created by: Codex
Last Modified at: 2026-07-08 22:36 EDT
Last Modified by: Codex

## topic frontend jank from always-on work

## Q1. What does "frontend carding" mean operationally here?
- It means visible stutter or sluggish interaction caused by unnecessary main-thread work, frequent React renders, or avoidable network-triggered state updates on normal pages.
- Recommended answer: measure and fix always-on work first because it affects every page, then leave deeper page-specific profiling for later loops.

## Q2. Which code paths are always-on?
- The global header is mounted on normal app pages and polls active games for logged-in users.
- The desktop pet can be mounted globally and moves through `requestAnimationFrame`.
- Recommended answer: fix global header polling cadence and cat movement render strategy before smaller page-local issues.

## Q3. Why is header polling risky?
- It currently runs every 5 seconds on every logged-in page, even when the page is hidden, and it calls `setCurrentGame` for every response. That creates network load plus React updates unrelated to the user's current task.
- Recommended answer: only poll while authenticated, visible, and not already in-flight; use slower idle cadence and faster active-game cadence; skip state updates when the payload did not change.

## Q4. Why is the cat pet risky?
- Its movement engine calls `setPosition` on every animation frame during long movement periods. That pushes React updates at frame rate across the whole mounted component tree area.
- Recommended answer: keep animation in `requestAnimationFrame`, but write position via a CSS transform ref and only keep logical position in refs/state at interaction boundaries.

## Q5. What should not be mixed into this loop?
- Full page redesign, engine worker infrastructure, predictor work, and multi-user study collaboration are separate todos.
- Recommended answer: keep this loop bounded to measurable jank reduction and deploy it.

## Q6. What verifies this?
- Frontend build passes.
- Source inspection confirms header polling throttling and no per-frame React `setPosition` in cat movement callbacks.
- Production deploy smoke confirms the app and API still respond.
