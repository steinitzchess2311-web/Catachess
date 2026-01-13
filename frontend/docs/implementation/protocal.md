# Catachess Development Protocol (v1.0)

> **Mandate:** This document defines the strict architectural boundaries for the Catachess reconstruction. Any deviation is a failure of the "Vertical Slice" architecture.

---

** You should follow ALL files in this folder to implement. After finishing a checkbox, write a "x" in the checkbox showing you have finished. After finishing each stage, write a working summary IN implementation/summaries. EACH STAGE HAS ITS OWN SUMMARY. for instance, after you finish phase 0, create summaries/phase0.md

## 1. Strict Frontend-Backend Separation
Frontend and Backend must communicate **exclusively** via HTTP REST or WebSockets.

*   **No Coupling:** The frontend code must never contain Python path logic, and the backend must never generate HTML (except for email templates).
*   **API Only:** All data must be fetched through the `ApiClient` singleton.
*   **State Ownership:** The Backend is the "Source of Truth" for data. The Frontend is the "Source of Truth" for UI state.

---

## 2. Module Internal Separation (The Triad)
Every module in `frontend/ui/modules/{module_name}/` MUST adhere to the following file structure. Crossing these boundaries is strictly forbidden.

### A. `layout/index.html` (The Skeleton)
*   **Restriction:** MUST only contain `<template>` tags or static HTML fragments.
*   **Restriction:** NO inline styles (`style="..."`).
*   **Restriction:** NO inline scripts (`onclick="..."`).
*   **Purpose:** Pure structure. Logic is injected by the Events layer.

### B. `styles/index.css` (The Skin)
*   **Restriction:** MUST use CSS Variables from `ui/assets/variables.css` for all colors, spacing, and typography.
*   **Restriction:** NO "Magic Numbers" (e.g., `margin-left: 13px;` is banned; use `var(--space-md)`).
*   **Restriction:** Scoped classes only (prefix classes with the module name, e.g., `.study-board-container`).

### C. `events/index.ts` (The Brain)
*   **Restriction:** NO HTML strings (e.g., `element.innerHTML = "<div>...</div>"` is BANNED).
*   **Requirement:** Use `document.importNode(template.content, true)` to clone structure from `layout/`.
*   **Requirement:** All API calls must go through the centralized `ApiClient`.
*   **Responsibility:** Event listeners, DOM manipulation (cloning/toggling), and Data orchestration.

---

## 3. Global Assets & Core
*   **`ui/assets/`**: Contains the design system (`variables.css`) and the `ApiClient`.
*   **`ui/core/`**: Provides foundational services (Drag, Resize, Focus). Modules should **consume** Core services, not reimplement them.

---

## 4. "Vertical Slice" Enforcement
*   Each feature (Auth, Workspace, Study) is a self-contained slice.
*   Shared components (like the Chessboard or Discussion panel) must be treated as independent modules that are **imported** by other slices.
*   **Purge Rule:** Any code found outside this structure (e.g., the legacy `games` folder) must be deleted immediately.

---

## 5. Development Workflow
1.  **Layout First:** Define the structure in `<template>`.
2.  **Style Second:** Apply the "Google Look" using variables.
3.  **Events Last:** Wire up the logic and API calls.
4.  **Verification:** Test against the Stage Checkboxes.
