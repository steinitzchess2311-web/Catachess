# Catachess Frontend Reconstruction Plan (Final Corrected)

> **Author:** Senior UI/UX Architect
> **Date:** 2026-01-12
> **Objective:** Re-architect the frontend using **Strict Vertical Slices** with sub-folders (`layout/`, `events/`, `styles/`).
> **CRITICAL:** Preserve existing `ui/core` (Window Management System) and `ui/modules/chessboard`.

---

## 0. 🚨 URGENT Backend Fixes (Blockers)

The frontend **cannot function** without these backend routes. Fix these first.

1.  **Mount `Versions` Router:**
    *   **File:** `backend/modules/workspace/api/router.py`
    *   **Action:** Add `from workspace.api.endpoints import versions` and `api_router.include_router(versions.router)`.

2.  **Mount `Presence` Router:**
    *   **File:** `backend/modules/workspace/api/router.py`
    *   **Action:** Add `from workspace.api.endpoints import presence` and `api_router.include_router(presence.router)`.

---

## 1. 🗑️ Demolition Squad (Files to Remove)

Clean up the old structure to make way for the new strictly organized modules.

*   **DELETE ENTIRELY:** `frontend/ui/modules/workspace/` (Old implementation)
*   **DELETE:** `frontend/ui/examples/` (Dead code)
*   **DELETE:** `frontend/workspace-select.html` (Redundant)
*   **DELETE:** `frontend/planAndImplement.md`, `frontend/IMPLEMENTATION_SUMMARY.md`

**⚠️ STRICTLY PRESERVE:**
*   `frontend/ui/core/` (drag, resize, focus, pointer, scroll, utils)
*   `frontend/ui/modules/chessboard/`

---

## 2. 🏗️ Architecture & File Structure

We strictly follow the **Vertical Slice** pattern with dedicated sub-folders.

### Root Level
*   `frontend/index.html`: Entry point. Redirects based on Auth.

### Core Systems (`frontend/ui/core/`) - **PRESERVED**
*   `drag/`: Element dragging logic.
*   `focus/`: Z-index and focus management.
*   `pointer/`: Unified pointer events.
*   `resize/`: Resizing handles.
*   `scroll/`: Smooth scrolling.
*   `utils/`: Snapping & Window state.

### Shared Assets (`frontend/ui/assets/`)
*   `css/variables.css`: Design tokens (Colors, Spacing).
*   `js/api.ts`: Singleton API Client (Fetch wrapper with Auth).

### Modules (The Vertical Slices)

#### 1. Auth Module (`frontend/ui/modules/auth/`)
*   **Login Sub-module:** `frontend/ui/modules/auth/login/`
    *   `layout/index.html`: Login card HTML.
    *   `events/index.ts`: Handles form submit -> `api.post('/auth/login')`.
    *   `styles/index.css`: Material input styles.
*   **Signup Sub-module:** `frontend/ui/modules/auth/signup/`
    *   `layout/index.html`: Registration form.
    *   `events/index.ts`: Handles `api.post('/auth/register')`.
    *   `styles/index.css`: Consistent styling.

#### 2. Home Module (`frontend/ui/modules/home/`)
*   `layout/index.html`: Landing page structure.
*   `events/index.ts`: "Get Started" navigation.
*   `styles/index.css`: Hero section styles.

#### 3. Workspace Module (`frontend/ui/modules/workspace/`)
*   `layout/index.html`: Sidebar + Grid container.
*   `events/index.ts`:
    *   Fetches nodes via `api.get('/nodes')`.
    *   Uses `ui/core` for any floating panels (e.g., "New Folder" modal).
*   `styles/index.css`: Grid layout, Card design.
*   `components/`:
    *   `card/`: Helper to generate Folder/Study card HTML.

#### 4. Study Module (`frontend/ui/modules/study/`)
*   `layout/index.html`: Chess interface container.
*   `events/index.ts`:
    *   Initializes `ui/modules/chessboard`.
    *   Uses `ui/core` to create draggable/resizable panels (Chat, Engine).
    *   Connects to Backend `GET /studies/{id}`.
*   `styles/index.css`: Dark mode / Focus mode styles.

---

## 3. 🧬 Data Flow & Relationships

### Module -> Core Relationship
Modules utilize the capabilities of `ui/core` to build rich interfaces.
*   **Example:** `modules/study` wants a movable Chat window.
    *   It **DOES NOT** write drag logic.
    *   It **IMPORTS** `createPanel` from `ui/core`.
    *   `const chatPanel = createPanel({ element: chatDiv, draggable: true });`

### Module -> Backend Relationship
All modules use the singleton API client.
*   **Location:** `frontend/ui/assets/js/api.ts`
*   **Usage in Events:**
    ```typescript
    import { api } from '../../../assets/js/api.js';
    // Inside an event handler
    const data = await api.post('/nodes', payload);
    ```

### Module -> Chessboard Relationship
The `study` module is the consumer of the `chessboard` module.
*   `modules/study/events/index.ts` imports `createChessboard` from `ui/modules/chessboard`.
*   It passes a DOM element from `modules/study/layout/index.html` to initialize the board.

---

## 4. 🎨 Design System (Google Material 3)

**Colors:**
*   `--primary`: `#1A73E8`
*   `--surface`: `#FFFFFF`
*   `--background`: `#F8F9FA`

**Typography:**
*   `--font-sans`: "Google Sans", "Roboto", sans-serif.

**Components:**
*   **Buttons:** Pill-shaped or slightly rounded (`8px`).
*   **Inputs:** Outlined with floating labels.
*   **Panels (via Core):** White surface, shadow-2 elevation, rounded corners (`12px`).

---

## 5. Implementation Roadmap

1.  **Backend:** Fix `router.py` (Versions & Presence).
2.  **Cleanup:** Delete `frontend/ui/modules/workspace`, `examples`, `workspace-select.html`.
3.  **Assets:** Create `api.ts` and `variables.css`.
4.  **Auth:** Rebuild Login/Signup with the `layout/`, `events/`, `styles/` folder structure.
5.  **Home:** Implement Home module.
6.  **Workspace:** Rebuild with new structure, connecting to `/nodes` API.
7.  **Study:** Rebuild, integrating `ui/core` for panels and `ui/modules/chessboard` for the game.