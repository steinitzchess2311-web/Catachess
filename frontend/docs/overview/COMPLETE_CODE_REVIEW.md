# Catachess Complete Code Review

> **Date:** January 12, 2026
> **Scope:** Full Repository Audit
> **Status:** Critical Issues Identified

---

## 1. Code Structure & File Manifest

### **Root Directory**
*   `Procfile`: Production entry point for Railway, launches `backend/main.py`.
*   `requirements.txt`: Python dependencies.
*   `railway.toml`: Deployment configuration for Railway.
*   `pytest.ini` / `conftest.py`: Testing configuration.

### **Backend (`backend/`)**
The core logic of the application, built with FastAPI.

*   `main.py`: **Entry Point.** The production FastAPI app that registers all routers and middleware.
*   `app/app.py`: **Legacy/Duplicate.** A secondary FastAPI app definition, likely a vestige or for testing. *Potential confusion point.*
*   `init_game_tables.py` / `init_verification_table.py`: Scripts to initialize database schemas on startup.

#### **Core (`backend/core/`)**
Shared utilities and domain-agnostic logic.
*   `config.py`: Global application settings (env vars).
*   `db/`: Database session management (SQLAlchemy).
*   `security/`: JWT handling, password hashing, and user permissions.
*   `chess_engine/`: **Stockfish Integration.**
    *   `orchestrator/`: Manages multiple engine "spots" (instances) for load balancing.
    *   `spot/`: Represents a single engine instance.
    *   `client.py`: The main interface used by the router.
*   `chess_basic/`: Pure Python chess rules and PGN parsing logic.
*   `tagger/`: Advanced chess position analysis and tagging system (prophylaxis, tactical motifs).

#### **Modules (`backend/modules/`)**
Domain-specific business logic (Vertical Slices).
*   `workspace/`: **The "Google Drive for Chess" feature.**
    *   `api/router.py`: **CRITICAL ISSUE.** The main router for this module. *Missing `versions` and `presence` routes.*
    *   `api/endpoints/`: Individual route handlers (`nodes.py`, `studies.py`, etc.).
    *   `services/`: Business logic layer.
    *   `models/` & `schemas/`: Database models and Pydantic schemas.

#### **Routers (`backend/routers/`)**
Top-level API route definitions (wiring Services to HTTP).
*   `auth.py`: Authentication endpoints (Login, Signup, Verify).
*   `chess_engine.py`: Exposes `POST /analyze` to the frontend.
*   `assignments.py`: Managing homework/tasks.
*   `game_storage.py`: Saving/Loading games.

### **Frontend (`frontend/`)**
The client-side application (HTML/TS/CSS). **Currently in reconstruction.**

*   `ui/COMPLETE_PLAN.md`: The architectural blueprint.
*   `ui/core/`: Shared low-level UI utilities (drag-and-drop, focus management).
*   `ui/modules/`: Feature-specific UI components.
    *   `chessboard/`: The actual board rendering logic.
    *   `auth/`: Login/Signup forms.
    *   `games/`: **DEPRECATED.** Found in codebase but marked for deletion in the Plan.
    *   **MISSING:** `study/` and `discussion/` directories are required by the Plan but do not exist.
*   `ui/assets/`: **MISSING.** Should contain `variables.css`.

### **Tests (`tests/`)**
Comprehensive test suite.
*   `unit/`: Fast, isolated tests.
*   `integration/`: Tests checking database/API interactions.
*   `chess_engine/`: Specific tests for the orchestrator and failover logic.

---

## 2. Basic Data Flows

### **A. Stockfish Analysis Flow**
How the user gets a move recommendation.
1.  **Frontend:** User makes a move or clicks "Analyze".
2.  **API Call:** Frontend sends `POST /api/engine/analyze` with FEN, depth, and multipv.
3.  **Router:** `backend/routers/chess_engine.py` receives the request.
4.  **Core:** Calls `core.chess_engine.get_engine().analyze(...)`.
5.  **Orchestrator:** The engine client checks available "spots" (servers) in `spots.json` or config.
    *   It selects the best available spot (lowest latency/load).
6.  **Execution:** The request is sent to the selected external engine service.
7.  **Return:** JSON response with Principal Variations (PV) is returned to the frontend.

### **B. User Authentication Flow**
How a user signs up.
1.  **Frontend:** User submits email on `signup.html`.
2.  **API Call:** `POST /auth/register`.
3.  **Router:** `backend/routers/auth.py` validates input.
4.  **Service:** `backend/services/signup_verification_service.py` generates a code.
5.  **Storage:** Code and temporary user data are stored in DB.
6.  **Email:** A mock or real email is "sent" (logged or saved to `backend/templates/emails/`).
7.  **Verification:** User enters code -> `POST /auth/verify-signup` -> User is created in `users` table -> JWT token issued.

### **C. Workspace/Study Flow (Broken)**
How a user opens a study.
1.  **Frontend:** User navigates to a study.
2.  **API Call:** Should call `GET /studies/{id}` and `GET /versions/...` and connect to `WebSocket /presence`.
3.  **Router:** `backend/modules/workspace/api/router.py` is responsible for routing these.
4.  **FAILURE:** The `versions` and `presence` routes are not mounted in the router, causing 404 errors for those specific features.

---

## 3. Potential Issues & Action Items

### **CRITICAL (Blockers)**
1.  **Backend Routing:** `backend/modules/workspace/api/router.py` does not include `versions` and `presence` routers. This breaks the Study and Collaboration features.
2.  **Frontend Structure:**
    *   `ui/modules/games` exists (should be deleted).
    *   `ui/modules/study` and `ui/modules/discussion` are missing (need scaffolding).
    *   `ui/assets/variables.css` is missing (styles will break).

### **High Priority**
3.  **Duplicate App Entry:** `backend/app/app.py` exists alongside `backend/main.py`. This is confusing. Recommend deleting or renaming `app/app.py` to avoid accidental usage.
4.  **Missing Documentation:** `CODE_REVIEW.md` was referenced but missing. (This file replaces it).

### **Observations**
5.  **Stockfish Architecture:** The "Multi-Spot" architecture is robust, allowing failover. This is a strong point.
6.  **Testing:** Test coverage seems high, especially for the complex `chess_engine` logic.
