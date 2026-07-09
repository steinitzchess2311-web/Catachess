# Jul 8 Todo Completion Requirements
Created at: 2026-07-08 21:41 EDT
Created by: Codex
Last Modified at: 2026-07-08 21:41 EDT
Last Modified by: Codex

## brief intro
- goal: Define how `patch/docs/Jul_8_代办.md` must be completed without weakening production quality.
- 架构思路: Treat the todo list as a set of independently verifiable production changes, not as a single speculative refactor.

## requirements
- Each actionable todo line must be implemented to production quality before it is marked `-[✅]`.
- Each loop must preserve existing deployed behavior unless the todo explicitly changes it.
- Backend changes must avoid unbounded CPU, GPU, database, or request fan-out under concurrent use.
- Frontend redesign changes must follow the workspace/study product language and avoid explanatory clutter.
- Any item touching persistence, realtime editing, workers, or deployment must include server-side verification.
- Documentation must stay separate: requirements in `docs/requirements`, execution plans in `docs/plan`, and page design notes in `docs/pages_design`.
- The final todo file must show completion status inline in `patch/docs/Jul_8_代办.md`.

## folder structure
|-jul_8_todo_completion.md requirements for completing the Jul 8 todo file

## 代办
- Add item-specific requirements when a larger subsystem loop starts.
