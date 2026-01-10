# Quick Reference - Protocol Sync

## TL;DR

✅ **What got transferred:**
1. Protocol types → `types.ts`
2. Sample messages → `sample-messages.json`
3. Connection config → `connection-config.ts`

❌ **What did NOT get transferred:**
- Server implementation code
- Game logic
- Router code
- Storage code

---

## 1-Minute Integration Guide

### Copy to your frontend:

```bash
# From catachess/transferred_files/

# Required
cp types.ts frontend/ui/modules/games/modules/types.ts

# Recommended
cp connection-config.ts frontend/ui/modules/games/modules/connection.ts
cp sample-messages.json frontend/ui/modules/games/modules/__fixtures__/
```

### Use in your code:

```typescript
// Import types
import type { GameState, ServerMessage } from './modules/types';
import { WS_BASE } from './modules/connection';

// Connect
const ws = new WebSocket(`${WS_BASE}/game/${gameId}`);

// Handle messages
ws.onmessage = (event) => {
  const msg: ServerMessage = JSON.parse(event.data);

  if (msg.type === 'game_state') {
    const state: GameState = msg.payload;
    // Use state.position.fen, state.players, etc.
  }
};

// Send move
ws.send(JSON.stringify({
  type: 'move',
  game_id: 'xxx',
  player_id: 'yyy',
  seq: 1,
  payload: { move: 'e2e4' }
}));
```

---

## Key Type Exports

```typescript
// From types.ts

// Messages
MessageType           // Union of all message types
BaseMessage           // Base structure
ServerMessage         // game_state | error | ack
ClientMessage         // join | move | resign | etc.

// Game State
GameState             // Complete game state (from export_state())
PositionState         // Chess position (FEN, moves, turn)
PlayerInfo            // Player data
GameStateValue        // "waiting" | "active" | "ended"
GameResult            // "in_progress" | "white_wins" | etc.

// Specific Messages
GameStateMessage      // Server → Client: state update
MoveMessage           // Client → Server: make move
ErrorMessage          // Server → Client: error
```

---

## GameState Structure (Most Important)

```typescript
interface GameState {
  game_id: string;
  state: "waiting" | "active" | "ended";
  created_at: number;

  players: {
    [player_id: string]: {
      color: "white" | "black";
      player_id: string;
    }
  };

  position: {
    turn: "white" | "black";
    move_number: number;
    move_history: string[];    // ["e2e4", "e7e5", ...]
    fen: string;               // "rnbqkbnr/..."
    result: GameResult;
  };

  clock?: {
    white: number;   // seconds
    black: number;   // seconds
  };

  // Only if game ended
  ended_at?: number;
  end_reason?: string;
}
```

---

## Server Endpoints

```typescript
// From connection-config.ts

API_BASE = "https://iloveliquanhao.catachess.com"
WS_BASE  = "wss://iloveliquanhao.catachess.com/ws"

// Use like:
WebSocket(`${WS_BASE}/game/${gameId}`)
fetch(`${API_BASE}/api/games/${gameId}`)
```

---

## Sample Message Example

```json
{
  "type": "game_state",
  "game_id": "game_abc123",
  "player_id": "player_xyz789",
  "seq": 2,
  "payload": {
    "game_id": "game_abc123",
    "state": "active",
    "created_at": 1704672000,
    "players": {
      "player_xyz789": { "color": "white", "player_id": "player_xyz789" },
      "player_def456": { "color": "black", "player_id": "player_def456" }
    },
    "position": {
      "turn": "black",
      "move_number": 1,
      "move_history": ["e2e4"],
      "fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
      "result": "in_progress"
    },
    "clock": {
      "white": 600,
      "black": 600
    }
  }
}
```

---

## Message Flow

### Client joins game:

```
Client → Server: { type: "join", ... }
Server → Client: { type: "game_state", payload: { state: "waiting", ... } }
```

### Player makes move:

```
Client → Server: { type: "move", payload: { move: "e2e4" } }
Server → Client: { type: "ack", payload: { ack_seq: 2 } }
Server → Client: { type: "game_state", payload: { ... updated state ... } }
```

### Error:

```
Client → Server: { type: "move", payload: { move: "invalid" } }
Server → Client: { type: "error", payload: { code: "INVALID_MOVE", message: "..." } }
```

---

## Common Patterns

### Type guard for messages:

```typescript
function isGameStateMessage(msg: ServerMessage): msg is GameStateMessage {
  return msg.type === 'game_state';
}

if (isGameStateMessage(msg)) {
  // TypeScript knows msg.payload is GameState
  const fen = msg.payload.position.fen;
}
```

### Sequence tracking:

```typescript
class GameClient {
  private seq = 0;

  sendMessage(type: MessageType, payload: any) {
    this.ws.send(JSON.stringify({
      type,
      game_id: this.gameId,
      player_id: this.playerId,
      seq: ++this.seq,
      payload,
      timestamp: Date.now() / 1000
    }));
  }
}
```

### React hook example:

```typescript
function useGameState(gameId: string) {
  const [state, setState] = useState<GameState | null>(null);

  useEffect(() => {
    const ws = new WebSocket(`${WS_BASE}/game/${gameId}`);

    ws.onmessage = (event) => {
      const msg: ServerMessage = JSON.parse(event.data);

      if (msg.type === 'game_state') {
        setState(msg.payload);
      }
    };

    return () => ws.close();
  }, [gameId]);

  return state;
}
```

---

## Checklist

Before you start coding:

- [ ] Copy `types.ts` to your frontend
- [ ] Copy `connection-config.ts`
- [ ] Copy `sample-messages.json` (optional but helpful)
- [ ] Import types in your WebSocket client
- [ ] Test with sample messages first
- [ ] Connect to real server

---

## Need Help?

1. Check `sample-messages.json` for real examples
2. Check `README.md` for detailed explanations
3. Check server source files:
   - `game_server/ws_protocol/protocol_core/types.py`
   - `game_server/game/game_core/export.py`

**Remember:** Server is source of truth. Frontend mirrors protocol only.
