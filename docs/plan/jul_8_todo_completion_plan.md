# Jul 8 Todo Completion Plan
Created at: 2026-07-08 21:41 EDT
Created by: Codex
Last Modified at: 2026-07-08 21:41 EDT
Last Modified by: Codex

## brief intro
- goal: Implement `docs/requirements/jul_8_todo_completion.md`.
- 架构思路: Work in deployable loops, starting with bounded profile and UI bugs, then moving to persistence, performance, worker infrastructure, and predictor features.

## plan
- Keep tracked worktree changes scoped and ignore unrelated untracked files.
- For each loop, write a grill note, requirements document, plan document, and page design update when UI is touched.
- Implement only the loop's scoped code changes.
- Run targeted backend checks, frontend build checks, and screenshots where useful.
- Mark completed todo lines in `patch/docs/Jul_8_代办.md` only after verification.
- Commit and deploy after each production-ready loop.
- Defer marking engine, predictor, realtime permissions, and large redesign items until real infrastructure and compatibility checks are in place.

## folder structure
|-jul_8_todo_completion_plan.md loop plan for completing the Jul 8 todo file

## 代办
- Continue with engine worker, predictor, classroom, study permission, blog, chat, notification, and performance loops after the profile loop.
