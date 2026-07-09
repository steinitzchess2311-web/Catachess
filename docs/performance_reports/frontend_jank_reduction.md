# Frontend Jank Reduction Report
Created at: 2026-07-08 22:36 EDT
Created by: Codex
Last Modified at: 2026-07-08 22:36 EDT
Last Modified by: Codex

## scope
- Investigated obvious frontend jank sources in normal app usage.
- Focused on always-mounted components before page-local profiling.

## findings
- Global header active-game polling ran every 5 seconds for logged-in users regardless of tab visibility. Each response could trigger React state updates.
- Desktop pet movement used `requestAnimationFrame`, but each frame called `setPosition`, causing React render work during long movement/fall/drag sequences.

## changes
- Header active-game polling is adaptive:
  - 5 seconds while a game is waiting or ongoing.
  - 30 seconds while idle.
  - No polling while the tab is hidden.
  - No overlapping poll requests.
  - No state update when the response snapshot is unchanged.
- Desktop pet frame movement now writes `transform: translate3d(...)` through a DOM ref and stores the latest position in refs. React state updates remain for animation state, dragging state, direction, and rotation.
- Desktop pet behavior engine start is idempotent, so route/drag effects cannot stack multiple transition timers.
- Direction and rotation setters are guarded to avoid repeated same-value state work during long walks or climbs.

## expected impact
- Fewer global network requests and fewer unrelated React updates for logged-in users.
- Cat movement no longer causes frame-rate React re-renders during normal movement.

## residual risk
- Study move-tree and large PGN rendering still need deeper trace-based profiling in future loops.
