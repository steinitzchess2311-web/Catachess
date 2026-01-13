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

## 0.2 🛡️ Protected Modules (Do NOT Delete)

The following modules **MUST be preserved**. They are used by the new system. **Deleting these will break everything.**

### `ui/core/` - Window Management Infrastructure
- **Functionality:** Drag (拖拽), Focus (焦点), Resize (调整大小)
- **Usage:** "New Folder" popups, Study panel dragging, all modal windows
- **Preservation Reason:** High-quality foundation code, stable API
- **Warning:** ⚠️ Deleting this module will cause all popup/modal functionality to fail

### `ui/modules/chessboard/` - Core Chess Logic
- **Functionality:** Board rendering, move validation, PGN parsing
- **Usage:** Study module board display, game analysis
- **Preservation Reason:** Core feature, already modular, stable and reliable
- **Warning:** ⚠️ Deleting this module will make the entire application unusable

**Verification Command:**
```bash
ls frontend/ui/core && ls frontend/ui/modules/chessboard && echo "✓ Protected modules exist"
```

---

## 0.3 🔗 API Reference (Frontend ↔ Backend)

**CRITICAL:** This section defines the exact API contracts. All frontend code **MUST** use these endpoints exactly as specified.

### API Base URL
- **Local Development:** `http://localhost:8000`
- **Production:** `https://api.catachess.com` (TBD)

### Authentication Header
All authenticated requests MUST include:
```
Authorization: Bearer <access_token>
```

Where `<access_token>` is obtained from `POST /auth/login`.

---

### 📝 AUTH Module APIs

#### POST /auth/register
**Purpose:** Register new user (Step 1 of signup)

**Request:**
```json
POST http://localhost:8000/auth/register
Content-Type: application/json

{
  "identifier": "user@example.com",
  "identifier_type": "email",
  "password": "SecurePassword123!",
  "username": "johndoe"
}
```

**Success Response (201 Created):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "johndoe",
  "identifier": "user@example.com",
  "role": "student",
  "verification_sent": true
}
```

**Error Responses:**
- `409 Conflict`: User already exists
  ```json
  {
    "detail": "User with this identifier already exists"
  }
  ```
- `400 Bad Request`: Invalid input

**Frontend Actions:**
1. Show success message: "Verification code sent to {email}"
2. Store `identifier` in memory (needed for verification)
3. Navigate to verification step (show code input)

---

#### POST /auth/verify-signup
**Purpose:** Verify signup with 6-digit code (Step 2 of signup)

**Request:**
```json
POST http://localhost:8000/auth/verify-signup
Content-Type: application/json

{
  "identifier": "user@example.com",
  "code": "123456"
}
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "Account verified successfully"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid/expired code
  ```json
  {
    "detail": "Invalid or expired verification code"
  }
  ```
- `404 Not Found`: User not found

**Frontend Actions:**
1. Show success message: "Account verified! You can now log in."
2. Navigate to login page

---

#### POST /auth/resend-verification
**Purpose:** Resend verification code

**Request:**
```json
POST http://localhost:8000/auth/resend-verification
Content-Type: application/json

{
  "identifier": "user@example.com"
}
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "Verification code sent successfully"
}
```

**Rate Limit:** 3 requests per 5 minutes per IP

**Frontend Actions:**
1. Disable "Resend" button for 60 seconds
2. Show countdown: "Resend available in 59s..."
3. Show success message when sent

---

#### POST /auth/login
**Purpose:** Login and obtain access token

**Request (OAuth2 Form Data):**
```
POST http://localhost:8000/auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=SecurePassword123!
```

**OR (JSON alternative):**
```json
POST http://localhost:8000/auth/login/json
Content-Type: application/json

{
  "identifier": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Success Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid credentials
  ```json
  {
    "detail": "Invalid credentials"
  }
  ```

**Frontend Actions:**
1. Store `access_token` in `localStorage.setItem('token', token)`
2. Store token type: `localStorage.setItem('tokenType', 'bearer')`
3. Navigate to `/workspace` (main app)

**Rate Limit:** 10 attempts per 5 minutes per IP

---

### 📂 WORKSPACE Module APIs

#### POST /nodes
**Purpose:** Create new node (folder or study)

**Request:**
```json
POST http://localhost:8000/nodes
Authorization: Bearer <token>
Content-Type: application/json

{
  "node_type": "folder",
  "title": "My Openings",
  "description": "Collection of opening repertoire",
  "parent_id": "root",
  "visibility": "private",
  "layout": null
}
```

**Node Types:**
- `"workspace"` - Root workspace
- `"folder"` - Folder
- `"study"` - Chess study

**Success Response (201 Created):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "node_type": "folder",
  "title": "My Openings",
  "description": "Collection of opening repertoire",
  "owner_id": "550e8400-e29b-41d4-a716-446655440000",
  "parent_id": "root",
  "visibility": "private",
  "layout": null,
  "created_at": "2026-01-12T20:00:00Z",
  "updated_at": "2026-01-12T20:00:00Z",
  "version": 1
}
```

**Error Responses:**
- `404 Not Found`: Parent not found
- `403 Forbidden`: No permission to create in parent

---

#### GET /nodes/{node_id}/children
**Purpose:** Get children of a node (for folder navigation)

**Request:**
```
GET http://localhost:8000/nodes/550e8400-e29b-41d4-a716-446655440001/children
Authorization: Bearer <token>
```

**Success Response (200 OK):**
```json
{
  "nodes": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440002",
      "node_type": "folder",
      "title": "Sicilian Defense",
      "description": "",
      "owner_id": "...",
      "parent_id": "550e8400-e29b-41d4-a716-446655440001",
      "visibility": "private",
      "created_at": "2026-01-12T20:05:00Z",
      "version": 1
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440003",
      "node_type": "study",
      "title": "Najdorf Variation",
      "description": "Sharp attacking lines",
      "owner_id": "...",
      "parent_id": "550e8400-e29b-41d4-a716-446655440001",
      "visibility": "private",
      "created_at": "2026-01-12T20:10:00Z",
      "version": 1
    }
  ],
  "total": 2
}
```

**Frontend Actions:**
1. Render folders with folder icon
2. Render studies with study icon
3. Click folder → Navigate to folder's children
4. Click study → Navigate to `/study/{study_id}`

---

#### GET /nodes/{node_id}
**Purpose:** Get single node details

**Request:**
```
GET http://localhost:8000/nodes/550e8400-e29b-41d4-a716-446655440001
Authorization: Bearer <token>
```

**Success Response:** (Same structure as POST /nodes response)

---

#### PUT /nodes/{node_id}
**Purpose:** Update node (rename, change description)

**Request:**
```json
PUT http://localhost:8000/nodes/550e8400-e29b-41d4-a716-446655440001
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "My Openings (Updated)",
  "description": "Updated description",
  "visibility": "private",
  "layout": null,
  "version": 1
}
```

**Success Response (200 OK):** Updated node object

**Error Responses:**
- `409 Conflict`: Optimistic lock error (version mismatch)
  ```json
  {
    "detail": "Node was modified by another user. Please refresh."
  }
  ```
- `403 Forbidden`: No permission

**Frontend Actions on 409:**
1. Show error: "This item was modified by another user"
2. Offer "Refresh" button to reload

---

#### DELETE /nodes/{node_id}
**Purpose:** Soft delete node

**Request:**
```
DELETE http://localhost:8000/nodes/550e8400-e29b-41d4-a716-446655440001?version=1
Authorization: Bearer <token>
```

**Success Response (204 No Content):** Empty body

---

#### POST /nodes/{node_id}/move
**Purpose:** Move node to new parent

**Request:**
```json
POST http://localhost:8000/nodes/550e8400-e29b-41d4-a716-446655440002/move
Authorization: Bearer <token>
Content-Type: application/json

{
  "new_parent_id": "550e8400-e29b-41d4-a716-446655440003",
  "version": 1
}
```

**Success Response (200 OK):** Updated node object

---

### 📚 STUDY Module APIs

#### GET /studies/{study_id}
**Purpose:** Get study with all chapters and moves

**Request:**
```
GET http://localhost:8000/studies/550e8400-e29b-41d4-a716-446655440003
Authorization: Bearer <token>
```

**Success Response (200 OK):**
```json
{
  "study": {
    "id": "550e8400-e29b-41d4-a716-446655440003",
    "title": "Najdorf Variation",
    "description": "Sharp attacking lines",
    ...
  },
  "chapters": [
    {
      "id": "chapter-1",
      "title": "Main Line",
      "pgn": "1. e4 c5 2. Nf3 d6 3. d4 cxd4 4. Nxd4 Nf6 5. Nc3 a6",
      "move_tree": { ... }
    }
  ]
}
```

**Frontend Actions:**
1. Initialize chessboard with first chapter
2. Render chapter list in sidebar
3. Parse PGN and display move tree

---

#### POST /studies/{study_id}/chapters/{chapter_id}/moves
**Purpose:** Add move to study

**Request:**
```json
POST http://localhost:8000/studies/{study_id}/chapters/{chapter_id}/moves
Authorization: Bearer <token>
Content-Type: application/json

{
  "parent_move_id": "move-123",
  "san": "Nf3",
  "uci": "g1f3",
  "fen_after": "rnbqkbnr/pppppppp/8/8/8/5N2/PPPPPPPP/RNBQKB1R b KQkq - 1 1"
}
```

**Success Response (201 Created):** Move object with `move_id`

---

### 💬 DISCUSSION Module APIs

#### GET /discussions
**Purpose:** Get discussion threads for target (study/chapter/move)

**Request:**
```
GET http://localhost:8000/discussions?target_type=study&target_id=550e8400...
Authorization: Bearer <token>
```

**Success Response (200 OK):**
```json
{
  "threads": [
    {
      "id": "thread-1",
      "author": {
        "id": "user-1",
        "username": "johndoe"
      },
      "content": "Great study! Very instructive.",
      "created_at": "2026-01-12T20:00:00Z",
      "reactions": {
        "👍": 5,
        "❤️": 2
      },
      "reply_count": 3
    }
  ]
}
```

---

#### POST /discussions
**Purpose:** Create new discussion thread

**Request:**
```json
POST http://localhost:8000/discussions
Authorization: Bearer <token>
Content-Type: application/json

{
  "target_type": "study",
  "target_id": "550e8400-e29b-41d4-a716-446655440003",
  "content": "Great study! Very instructive."
}
```

**Success Response (201 Created):** Thread object

---

#### POST /discussions/{thread_id}/replies
**Purpose:** Reply to thread

**Request:**
```json
POST http://localhost:8000/discussions/thread-1/replies
Authorization: Bearer <token>
Content-Type: application/json

{
  "content": "Thanks! Glad you found it helpful.",
  "parent_reply_id": null
}
```

**Success Response (201 Created):** Reply object

---

### ⏱️ PRESENCE & VERSIONS APIs

#### POST /presence/heartbeat
**Purpose:** Send presence heartbeat (real-time collaboration)

**Request:**
```json
POST http://localhost:8000/presence/heartbeat
Authorization: Bearer <token>
Content-Type: application/json

{
  "study_id": "550e8400-e29b-41d4-a716-446655440003",
  "cursor_position": {
    "chapter_id": "chapter-1",
    "move_id": "move-5"
  }
}
```

**Success Response (200 OK):** Presence data

**Frontend Actions:**
- Send every 30 seconds while study is open
- Show other users' cursors on board

---

#### GET /nodes/{node_id}/versions
**Purpose:** Get version history of node

**Request:**
```
GET http://localhost:8000/nodes/550e8400-e29b-41d4-a716-446655440001/versions
Authorization: Bearer <token>
```

**Success Response (200 OK):**
```json
{
  "versions": [
    {
      "version": 2,
      "title": "My Openings (Updated)",
      "changed_by": "johndoe",
      "changed_at": "2026-01-12T20:30:00Z"
    },
    {
      "version": 1,
      "title": "My Openings",
      "changed_by": "johndoe",
      "changed_at": "2026-01-12T20:00:00Z"
    }
  ]
}
```

---

### ⚠️ Error Handling (Universal)

All endpoints may return these errors:

**401 Unauthorized:**
```json
{
  "detail": "Invalid or expired token"
}
```
**Frontend Action:** Clear `localStorage`, redirect to `/login`

**403 Forbidden:**
```json
{
  "detail": "You do not have permission to perform this action"
}
```
**Frontend Action:** Show error message, do not retry

**429 Too Many Requests:**
```json
{
  "detail": "Rate limit exceeded. Please try again later."
}
```
**Frontend Action:** Show error with retry countdown

**500 Internal Server Error:**
```json
{
  "detail": "An unexpected error occurred"
}
```
**Frontend Action:** Show generic error, log to console, provide "Retry" button

**503 Service Unavailable:**
```json
{
  "detail": "Service temporarily unavailable"
}
```
**Frontend Action:** Show "Service down" message, auto-retry after 10s

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

---

## 8. 🛠️ IMPLEMENTATION ADDENDUM (Post-Audit)

### A. Cleanup & Purge
*   **Remove Legacy:** Delete `frontend/ui/modules/games/`. It is non-standard and deprecated by the Vertical Slice mandate.
*   **Audit Check:** Any file in `ui/modules/` not listed in Section 1 must be removed.

### B. Initialization Tasks
1.  **Scaffold New Modules:** Create `study/` and `discussion/` folders in `ui/modules/` with the standard `layout/`, `events/`, and `styles/` sub-directories.
2.  **Asset Creation:** Initialize `frontend/ui/assets/` directory. Create `variables.css` using the specifications in Section 2.

### C. Verification Checklist
- [ ] **Backend:** Verify `GET /nodes/.../versions` and `POST /presence` are reachable via `/docs`.
- [ ] **Structure:** Ensure `ui/modules/games` is removed.
- [ ] **Styles:** Confirm `variables.css` is correctly linked in `index.html`.
