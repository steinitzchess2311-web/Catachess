# Catachess Frontend Reconstruction Plan (Final Specs & Design System)

> **Author:** Senior Product Manager (Ex-Google Design/Eng)
> **Date:** 2026-01-12
> **Status:** FINAL APPROVED VERSION
> **Strict Mandate:** Preserve `ui/core` and `ui/modules/chessboard`. Use Vertical Slice with sub-folders (`layout/`, `events/`, `styles/`).

---

## 0. 🚨 URGENT Backend Fixes (Blockers)

The frontend **cannot function** without these backend routes. Fix these first.

1.  **Mount `Versions` & `Presence` Routers:**
    *   **File:** `backend/modules/workspace/api/router.py`
    *   **Action:** Add `from workspace.api.endpoints import versions, presence` and include them in `api_router`.
    *   **Why:** `study.html` relies on these for history and real-time collaboration.

---

## 1. 📂 GLOBAL FILE STRUCTURE

Strict Vertical Slice with sub-folders. Anything else must be purged.

```text
frontend/
├── index.html                  # Shell + Auth Router
├── ui/
│   ├── assets/                 # variables.css (Material 3), api.ts (Singleton)
│   ├── core/                   # [PRESERVED] Window Management (drag, focus, resize, etc.)
│   └── modules/
│       ├── chessboard/         # [PRESERVED] Chess logic & rendering
│       ├── auth/
│       │   ├── login/          # layout/, events/, styles/
│       │   └── signup/         # layout/, events/, styles/ (Includes Verification)
│       ├── workspace/          # layout/, events/, styles/
│       ├── study/              # layout/, events/, styles/ (Board + Chapters + PGN)
│       └── discussion/         # layout/, events/, styles/ (Shared Component)
```

---

## 2. 🎨 DESIGN SYSTEM SPECIFICATIONS (The "Google" Look)

**MANDATORY:** All styles must use these CSS variables. No magic numbers or hardcoded hex values in module CSS files.

### A. Color Palette (Material 3 Adaptive)
*   **Primary (Action):** `--primary: #1A73E8;` (Google Blue)
    *   `--primary-hover: #174EA6;`
    *   `--primary-bg: #E8F0FE;` (Light blue background for active states)
*   **Surface (Cards/Panels):** `--surface: #FFFFFF;`
*   **Background (App):** `--bg-app: #F8F9FA;` (Gray 50 - provides contrast for cards)
*   **Text (Typography):**
    *   `--text-main: #202124;` (Gray 900 - Almost Black)
    *   `--text-secondary: #5F6368;` (Gray 700 - Muted info)
    *   `--text-disabled: #DADCE0;`
*   **Borders:** `--border: #DADCE0;` (Light Gray)
*   **States:**
    *   `--success: #1E8E3E;` (Green 600)
    *   `--error: #D93025;` (Red 600)
    *   `--warning: #F9AB00;` (Yellow 600)

### B. Typography (Zi Ti Daxiao)
*   **Font Family:** `font-family: 'Google Sans', 'Roboto', -apple-system, sans-serif;`
*   **Scale:**
    *   `--font-xs: 12px;` (Labels, Meta info)
    *   `--font-sm: 14px;` (Body text, Inputs)
    *   `--font-md: 16px;` (Headers within cards)
    *   `--font-lg: 20px;` (Page Titles)
    *   `--font-xl: 24px;` (Hero text)
*   **Line Heights:** 1.5 for body, 1.2 for headings.

### C. Shape & Radius (Yuan Jiao)
*   **Buttons:** `--radius-pill: 20px;` (Rounded "Pill" shape for primary actions)
*   **Inputs:** `--radius-sm: 4px;` (Slightly rounded corners)
*   **Cards/Panels:** `--radius-md: 8px;` (Standard container radius)
*   **Modals:** `--radius-lg: 16px;` (Large floating surfaces)

### D. Spacing & Layout (Jianju)
*   **Grid System:** Base unit 4px.
    *   `--space-xs: 4px;`
    *   `--space-sm: 8px;`
    *   `--space-md: 16px;` (Standard padding)
    *   `--space-lg: 24px;`
    *   `--space-xl: 32px;`
*   **Gap:** Use `gap: var(--space-md);` in Flex/Grid layouts.

### E. Elevation & Shadows (Yinying)
*   **Flat (Border only):** Inputs, Sidebar items.
*   **Level 1 (Card):** `box-shadow: 0 1px 2px 0 rgba(60,64,67,0.3), 0 1px 3px 1px rgba(60,64,67,0.15);`
*   **Level 2 (Hover/Dropdown):** `box-shadow: 0 4px 8px 3px rgba(60,64,67,0.15);`
*   **Level 3 (Modal/Draggable):** `box-shadow: 0 8px 16px 4px rgba(60,64,67,0.15);`

---

## 3. 🛡️ MODULE: AUTH -> SIGNUP (`ui/modules/auth/signup/`)

**Workflow:** 2-Step Authentication Flow.

### ⚡ Events & Logic (`events/index.ts`)

| Action | Trigger | UI State | Backend Path | Logic Detail |
| :--- | :--- | :--- | :--- | :--- |
| **Register** | Submit Form | Disable btn, show spinner | `POST /auth/register` | If success -> `showStep(2)`, `startTimer()`. Store email in memory. |
| **Verify** | Input 6 chars | Overlay loading | `POST /auth/verify-signup` | Send `{ identifier: email, code: code }`. Success -> Redirect to Login. |
| **Resend** | Click Link | Disable link for 60s | `POST /auth/resend-verification` | Send `{ identifier: email }`. Restart 60s countdown. |

---

## 4. 💬 MODULE: DISCUSSION (`ui/modules/discussion/`)

**Concept:** A context-aware panel that slides in from the right or appears in a designated `.comment-box`.

### 🎨 Design Specs
*   **Layout:** Vertical thread list. Avatars (40px, circle), Markdown content, Reply links (blue text).
*   **Integration:** In `study.html`, it lives in the `.comment-box`. In `folder.html`, it is toggled via the `.discussion-toggle`.

### ⚡ Events & Logic (`events/index.ts`)

| Action | Trigger | Backend Path | Logic Detail |
| :--- | :--- | :--- | :--- |
| **Load** | Toggle Open | `GET /discussions?target={id}` | Fetches threads. Recursively renders replies (max 5 depth). |
| **Post** | Click "Send" | `POST /discussions` | Creates a new thread at the current context (Study/Chapter/Move). |
| **Reply** | Click "Reply" | `POST /discussions/{tid}/replies` | Posts a reply to a specific thread or parent reply. |
| **React** | Click Emoji | `POST /reactions` | Optimistic UI: Update count immediately, then send `{ target_id, emoji }`. |

---

## 5. ♟️ MODULE: STUDY (`ui/modules/study/`)

**Concept:** Highly adjustable layout with a **Forced Square Board**.

### 🎨 Design Specs
*   **Proportions:** Managed via `grid-template-columns: 240px 1fr 280px`.
*   **The Board:** `aspect-ratio: 1/1` constraint. Must remain square regardless of window size.
*   **Visibility:** All panels (Chapters, PGN, Sidebar) have `.hide-btn`.

### ⚡ Events & Logic (`events/index.ts`)

| Action | Trigger | UI Interaction | Logic Detail |
| :--- | :--- | :--- | :--- |
| **Toggle UI** | Click `.hide-btn` | Animate width to 0 | Collapse/Expand panels. Adjust grid columns dynamically. |
| **Move** | Drag on Board | `POST /studies/.../moves` | Update PGN tree. Trigger **Discussion** context update to current move. |
| **Init** | Page Load | `GET /studies/{id}` | Hydrate Board, Chapters, and PGN. Trigger **Presence** heartbeat. |

---

## 6. 🗂️ MODULE: WORKSPACE (`ui/modules/workspace/`)

### ⚡ Events & Logic (`events/index.ts`)

| Action | Trigger | Backend Path | Logic Detail |
| :--- | :--- | :--- | :--- |
| **List** | Init / Navigate | `GET /nodes?parent_id={id}` | Renders Folders and Studies. |
| **Create** | "Add" buttons | `POST /nodes` | Type `workspace`, `folder`, or `study`. |

---

## 7. 💻 DEVELOPER GUIDELINES

1.  **Strict Layout Separation:** No HTML strings in `events/index.ts`. Use `<template>` elements from `layout/index.html`.
2.  **Core Usage:** When building the "New Folder" popup, **MUST** use `ui/core/drag` and `ui/core/focus` to make it a proper draggable window.
3.  **Styles:** All sizing **MUST** use variables from `assets/css/variables.css`. No hardcoded hex codes.
