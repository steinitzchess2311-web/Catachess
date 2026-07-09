## header
Created at: 2026-07-08 23:58:19 EDT
Created by: Codex
Last Modified at: 2026-07-08 23:58:19 EDT
Lst Modified by: Codex

## brief intro
- goal for this folder.
  - React classroom frontend module for classroom lists, classroom detail pages, assignments, members, invites, broadcasts, and teacher/student workflows.
- 架构思路
  - Keep API calls in `api.ts`, shared classroom data contracts in `types.ts`, page shells in `ClassroomPage.tsx` and `ClassroomDetailPage.tsx`, reusable UI/workflow pieces in `components/`, and visual primitives in `classroom.css`.
  - Classroom UI should follow the workspace/study product language: blue/white, compact, border-led, and operational.

## folder structure
|-ClassroomPage.tsx classroom list page with create/join entry points.
|-ClassroomDetailPage.tsx classroom detail shell with tabs and classroom-level actions.
|-api.ts API client wrapper for classroom backend endpoints.
|-classroom.css shared classroom visual system and layout primitives.
|-components/ classroom component subfolder. Another README doc is necessary in this subfolder.
|-docs/ local classroom design/action mapping notes.
|-intro.md implementation notes inherited from the original classroom module.
|-types.ts shared TypeScript data contracts.
|-utils.ts shared classroom UI utilities.
|-index.ts module exports.

## 代办
- Continue removing native browser dialogs from deeper assignment/member management flows.
- Keep classroom design aligned with workspace and study pages as those pages evolve.
