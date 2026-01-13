# Stage 1: Critical Setup & Blockers

> **Goal:** Clear all blockers, establish the global design system, and verify Stage 0 completion.
> **Dependencies:** Stage 0 (Legacy Cleanup) must be completed first.
> **Prerequisites:** Stage 0 完成（遗产清理完成）

## 0. Verify Stage 0 Completion

在开始 Stage 1 之前，必须确认 Stage 0 已正确完成：

- [ ] **Verify Protected Modules**:
    - [ ] `frontend/ui/core/` 存在
    - [ ] `frontend/ui/modules/chessboard/` 存在

- [ ] **Verify Archived Module**:
    - [ ] `frontend/ui/modules/games/` 存在
    - [ ] `frontend/ui/modules/games/README.md` 存在并包含 "ARCHIVED"

- [ ] **Verify Deleted Modules**:
    - [ ] `frontend/ui/modules/workspace/` 不存在
    - [ ] `frontend/ui/modules/login/` 不存在
    - [ ] `frontend/ui/modules/signup/` 不存在

- [ ] **Verify Git Tag**:
    - [ ] `git tag` 显示 `stage0-complete`

**如果任何一项验证失败，必须先完成 Stage 0，再继续 Stage 1。**

---

## 1. Backend Fixes (Blocker Removal)
The frontend cannot function until the API exposes the necessary routes.

- [ ] **Edit `backend/modules/workspace/api/router.py`**:
    - [ ] Import `versions` and `presence` from `workspace.api.endpoints`.
    - [ ] Include `versions.router` in `api_router`.
    - [ ] Include `presence.router` in `api_router`.
- [ ] **Verify Backend**:
    - [ ] Run the backend (`uvicorn main:app` or `cd backend && python main.py`).
    - [ ] Visit `http://localhost:8000/docs`
    - [ ] Confirm `GET /nodes/{id}/versions` exists in docs
    - [ ] Confirm `POST /presence/heartbeat` exists in docs

## 2. Frontend Module Structure Verification
Verify that the structure matches the Vertical Slice mandate after Stage 0 cleanup.

- [ ] **Verify Structure**:
    - [ ] Confirm `frontend/ui/modules/` only contains: `chessboard`, `games` (archived)
    - [ ] Confirm `workspace/`, `login/`, `signup/` do NOT exist (deleted in Stage 0)

## 3. Global Assets & Design System
Implement the "Google Look" specifications.

- [ ] **Create Directory**: `frontend/ui/assets/`.
- [ ] **Create File**: `frontend/ui/assets/variables.css`.
    - [ ] **Content**: Copy the exact CSS variables from `COMPLETE_PLAN.md` Section 2 (Colors, Typography, Shape, Spacing, Elevation).
- [ ] **Create File**: `frontend/ui/assets/api.ts`.
    - [ ] **Content**: Implement a Singleton `ApiClient` class that:
        - [ ] Handles `baseURL` (from environment or relative).
        - [ ] Intercepts requests to inject `Authorization: Bearer <token>`.
        - [ ] Handles 401 errors (redirect to login).

## 4. Module Scaffolding
Prepare the directories for future stages.

- [ ] **Create Directory**: `frontend/ui/modules/study/` with subfolders `layout`, `events`, `styles`.
- [ ] **Create Directory**: `frontend/ui/modules/discussion/` with subfolders `layout`, `events`, `styles`.
- [ ] **Create Directory**: `frontend/ui/modules/auth/` (if partial) ensuring `login` and `signup` subfolders exist with `layout`, `events`, `styles`.

## 5. Verification
- [ ] **Browser Check**: Open `index.html`. It should ideally be empty or a shell.
- [ ] **Link Styles**: Ensure `index.html` links to `<link rel="stylesheet" href="ui/assets/variables.css">`.
