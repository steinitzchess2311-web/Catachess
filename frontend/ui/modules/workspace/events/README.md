## header
Created at: 2026-07-08 18:02 EDT
Created by: Codex
Last Modified at: 2026-07-08 18:02 EDT
Last Modified by: Codex

## brief intro
- goal for this folder.
  - Runtime behavior for the legacy workspace module.
  - Coordinates rendering, navigation, node operations, search, modals, and React islands.
- 架构思路
  - Keep page state centralized in `state.ts`.
  - Use wrapper/orchestrator files to avoid direct circular calls across modules.
  - Keep visual rendering in `rendering.ts` and browser event wiring in `eventHandlers.ts`.

## folder structure
|-eventHandlers.ts DOM event binding for workspace controls
|-handlerWrappers.ts connects modal, node, rendering, and navigation modules
|-initialization.ts extracts DOM elements and enters the initial folder
|-navigation.ts breadcrumb and internal path utilities
|-nodeOperations.ts API calls and sorting helpers
|-orchestrator.ts creates coordinated handlers and React islands
|-reactComponents.ts mounts React controls inside the template
|-rendering.ts renders cards, empty states, and header state
|-search.ts workspace search behavior
|-state.ts workspace state helpers
|-types.ts shared workspace UI types

## 代办
- Keep hidden compatibility helpers separate from visible navigation controls.
