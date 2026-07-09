# Frontend Jank Reduction Requirements
Created at: 2026-07-08 22:36 EDT
Created by: Codex
Last Modified at: 2026-07-08 22:36 EDT
Last Modified by: Codex

## brief intro
- goal for this requirement: Reduce obvious frontend jank sources without changing user-facing workflows.
- 架构思路: Remove always-on unnecessary work first, because global components affect every page and every logged-in user.

## requirements
- Header active-game polling must not run while the browser tab is hidden.
- Header active-game polling must not start overlapping requests.
- Header active-game polling must be slower when there is no active game and faster only while a waiting or ongoing game exists.
- Header active-game polling must avoid React state updates when the response represents the same game state.
- Desktop pet movement must not call React state setters on every animation frame.
- Desktop pet drag/fall/walk visual position must remain smooth.
- No public UI text or navigation workflow should change in this performance loop.

## acceptance
- Header polling cadence is explicit in constants and page-visibility aware.
- Cat position is written with transform during frame updates and React state is reserved for logical state changes.
- `npm run build` in `frontend/web` passes.
- A production deploy smoke check returns 200 for the app/API after deployment.
