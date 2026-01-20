# Frontend Structure Improvements

- Define a single runtime entry HTML that loads `modules/ui/index.ts` (or built JS) and document it as the entrypoint, keeping `skeleton/skeleton.html` as a reference-only layout.
- Add a root wrapper (`#games-root`) or switch the renderer to use `#app-frame`, and centralize DOM lookups in a small adapter so renderers/events do not hardcode IDs.
- Update `frontend/ui/modules/games/README.md` to match the current `modules/core`, `modules/ui`, and `skeleton/` layout, removing references to the removed `layout/` and `styles/` trees.
- Move the inline CSS in `skeleton/skeleton.html` into a shared stylesheet (or add a `styles/` folder) so the runtime entry and skeleton stay in sync without duplicating layout rules.
- Add a single `ids.ts` (or similar) to declare and reuse region IDs across renderers/events, reducing drift when IDs change.

1
# Potential Issues

- `frontend/ui/modules/games/modules/ui/renderer.ts` writes connection state to `#games-root`, but the skeleton only defines `#app-frame`, so the dataset update never applies.
- There is no HTML file that imports `modules/ui/index.ts` or compiled JS, so the application cannot actually start without manual wiring or bundling.
- `frontend/ui/modules/games/README.md` still documents `layout/` and `styles/regions/` paths that no longer exist, which will mislead contributors and cause edits to dead files.
- Inline CSS in `skeleton/skeleton.html` makes it easy for the reference layout to diverge from any future runtime entry, creating two sources of truth for positioning.
- Renderers still use non-null assertions on IDs; any ID change or missing node will throw at startup without a centralized DOM validation step.
