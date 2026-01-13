# Stage 4: Study & Discussion Modules

> **Goal:** The core "Chess" experience. Board, Analysis, and Collaboration.
> **Dependencies:** Stage 3 (Workspace), `ui/modules/chessboard`.

## 1. Study Layout (`ui/modules/study/`)
- [ ] **Create `layout/index.html`**:
    - [ ] **Grid**: `240px 1fr 280px` (Sidebar, Board, Panels).
    - [ ] **Board Container**: Must force `aspect-ratio: 1/1` via CSS.
    - [ ] **Components**:
        - Left: Chapter List.
        - Center: Board (mount point).
        - Right: PGN / Analysis / Comments.
- [ ] **Create `styles/study.css`**:
    - [ ] Strict layout enforcement.
    - [ ] Collapsible panel classes.

## 2. Board Integration (`events/index.ts`)
- [ ] **Import**: `ui/modules/chessboard/Chessboard.ts` (or similar).
- [ ] **Initialize**:
    - [ ] `const board = new Chessboard(element, config)`.
    - [ ] Load PGN from API response (`GET /studies/{id}`).
- [ ] **Move Handling**:
    - [ ] On move -> `ApiClient.post('/studies/.../moves')`.
    - [ ] Update local state.

## 3. Discussion Module (`ui/modules/discussion/`)
- [ ] **Create `layout/index.html`**:
    - [ ] Thread List container.
    - [ ] Input Box (Markdown enabled).
- [ ] **Create `events/index.ts`**:
    - [ ] **Fetch**: `ApiClient.get('/discussions?target={study_id}')`.
    - [ ] **Post**: `ApiClient.post('/discussions')`.
    - [ ] **Context**: Listen to Board move events to update "current move context" for comments.

## 4. Real-time Presence
- [ ] **WebSocket**:
    - [ ] Connect to `ws://.../presence/{study_id}`.
    - [ ] **Handle Events**:
        - `cursor_move`: Show other user's mouse/selection.
        - `new_move`: Auto-update board.
        - `new_comment`: Push notification/update thread.

## 5. Verification
- [ ] **Full Loop**:
    1.  Open Study.
    2.  Make a move. Reload page. Move is there.
    3.  Post a comment "Good move".
    4.  Open 2nd browser window (Incognito).
    5.  See comment appear in real-time.
