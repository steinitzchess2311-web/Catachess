# Backend Requirements — user_games module

## 1. Cancel challenge / abort waiting game

**Problem**: `POST /api/game/{game_id}/abort` returns 400 when game is in `waiting` status
(opponent hasn't connected yet). The creator has no way to cancel.

**Needed**: Either:
- Allow `abort` in `waiting` status for the game creator, OR
- New endpoint: `POST /api/game/{game_id}/cancel` — only callable by creator, only in `waiting` status

**Response** (same as abort):
```json
{ "success": true, "game_id": "...", "status": "cancelled" }
```

---

## 2. Challenge invitation system (send / accept / decline)

Currently `POST /api/game/create` immediately creates a game — opponent has no chance to accept.
We need a proper challenge flow.

### New endpoints needed:

#### Send challenge
```
POST /api/challenge/send
Body: { "from_player": "alice", "to_player": "bob", "time_control": {...}, "color_preference": "random" }
Response 201: { "challenge_id": "uuid", "expires_at": "ISO8601" }
```

#### List pending challenges (for the challenged player)
```
GET /api/challenge/pending?user_id=bob
Response: [
  {
    "challenge_id": "uuid",
    "from_player": "alice",
    "time_control": { "initial": 300, "increment": 3 },
    "color_preference": "random",
    "expires_at": "ISO8601",
    "created_at": "ISO8601"
  }
]
```

#### Accept challenge → returns game_id to connect WebSocket
```
POST /api/challenge/{challenge_id}/accept
Body: { "user_id": "bob" }
Response 200: { "game_id": "uuid", "white_player_id": "alice", "black_player_id": "bob" }
```

#### Decline challenge
```
POST /api/challenge/{challenge_id}/decline
Body: { "user_id": "bob" }
Response 200: { "success": true }
```

**Notes**:
- Challenges expire after 5 minutes (configurable)
- A user can have multiple pending challenges
- Frontend polls `GET /api/challenge/pending` every 10s when user is online

---

## 3. Open game room (anyone can join without being specified as opponent)

For shareable game links — create a room, share the URL, anyone joins.

#### Create open game
```
POST /api/game/create-open
Body: { "player_id": "alice", "time_control": {...} }
Response 201: { "game_id": "uuid", "status": "open", "created_by": "alice" }
```

#### Join open game
```
POST /api/game/{game_id}/join
Body: { "user_id": "bob" }
Response 200: { "game_id": "uuid", "white_player_id": "...", "black_player_id": "..." }
Error 400: { "error": "game_already_started" }
Error 400: { "error": "cannot_join_own_game" }
```

**Notes**:
- Open games expire if no one joins within 10 minutes
- After join, both players connect via existing WebSocket endpoint
- `GET /api/game/{game_id}` should include `status: "open"` for this state

---

## 4. Public user profile endpoint ✅ DONE

~~Currently `GET /user/profile` only returns the **current authenticated user's** profile.~~
Implemented: `GET /user/profile/{username}` (no auth) in `backend/routers/user_profile.py`.
Also added `get_user_by_username()` in `backend/services/user_service.py`.

```
GET /user/profile/{username}   (no auth required)
Response 200: {
  "username": "liquanhao",
  "fide_title": "FM",
  "fide_rating": 2350,
  "cfc_rating": null,
  "ecf_rating": null,
  "chinese_athlete_title": "一级运动员",
  "lichess_username": "liquanhao",
  "chesscom_username": "liquanhao",
  "self_intro": "Chess player from ...",
  "created_at": "ISO8601"
}
Response 404: { "error": "user_not_found" }
```

**Notes**:
- No sensitive info (email, password hash, etc.)
- Used by `catachess.com/@liquanhao` public profile pages
