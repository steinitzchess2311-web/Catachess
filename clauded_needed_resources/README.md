# Transferred Files from Server

This directory contains protocol definitions and configurations synchronized from the game server.

## What's Included

### 1. `types.ts` - Protocol Type Definitions ⭐ MOST IMPORTANT

TypeScript mirror of the server's WebSocket protocol.

**Source:**
- `game_server/ws_protocol/protocol_core/types.py`
- `game_server/game/game_core/export.py`

**What it contains:**
- `MessageType` - All WebSocket message types
- `GameState` - Complete game state structure (mirrors `export_state()`)
- `PositionState` - Chess position information
- Client message types (`JoinMessage`, `MoveMessage`, etc.)
- Server message types (`GameStateMessage`, `ErrorMessage`, `AckMessage`)
- Type unions for all messages

**Usage:**
```typescript
import type { GameState, GameStateMessage, MoveMessage } from './types';

// Type your WebSocket handler
function handleServerMessage(msg: ServerMessage) {
  if (msg.type === 'game_state') {
    const state: GameState = msg.payload;
    // state.position.fen, state.players, etc.
  }
}
```

### 2. `sample-messages.json` - Real Message Examples

Real WebSocket message samples for testing and development.

**What it contains:**
- Example of every message type
- Multiple game states (waiting, active, ended)
- Error examples with different codes
- Realistic payloads with actual FEN strings and move history

**Usage:**
```typescript
import sampleMessages from './sample-messages.json';

// Use in tests
const mockState = sampleMessages.server_to_client.game_state_active;

// Use in Storybook/mock UI
const mockGameState: GameState = mockState.payload;
```

### 3. `connection-config.ts` - Server Connection Info

Server endpoints and connection configuration.

**What it contains:**
- `API_BASE` - HTTPS endpoint
- `WS_BASE` - WSS endpoint
- `WS_CONFIG` - Reconnection and heartbeat settings
- Helper functions for environment overrides

**Usage:**
```typescript
import { WS_BASE, API_BASE } from './connection-config';

// Connect to WebSocket
const ws = new WebSocket(`${WS_BASE}/game/${gameId}`);

// Make HTTP request
const response = await fetch(`${API_BASE}/api/games/${gameId}`);
```

## Integration into Your Frontend

### Step 1: Copy Types

Copy `types.ts` to your frontend module:

```bash
cp transferred_files/types.ts frontend/ui/modules/games/modules/types.ts
```

### Step 2: Copy Connection Config

```bash
cp transferred_files/connection-config.ts frontend/ui/modules/games/modules/connection.ts
```

### Step 3: Copy Sample Data (Optional)

```bash
mkdir -p frontend/ui/modules/games/modules/__fixtures__
cp transferred_files/sample-messages.json frontend/ui/modules/games/modules/__fixtures__/
```

## Important Principles

### 🚨 Server is Source of Truth

- **DO NOT** modify `types.ts` independently
- If protocol changes, update server first, then re-sync types
- Types are a **READ-ONLY MIRROR** of server protocol

### ✅ What You SHOULD Do

- Import types in your components
- Use sample messages for testing
- Build UI that consumes these types
- Write WebSocket client using these interfaces

### ❌ What You SHOULD NOT Do

- Copy server implementation code (`router.py`, `game_core/`, etc.)
- Run server code in frontend
- Modify types without updating server
- Hardcode message structures - always import from types

## Type Safety Example

```typescript
import type {
  GameState,
  ServerMessage,
  MoveMessage
} from './types';

class GameClient {
  private ws: WebSocket;

  sendMove(move: string) {
    const message: MoveMessage = {
      type: 'move',
      game_id: this.gameId,
      player_id: this.playerId,
      seq: this.nextSeq++,
      payload: { move },
      timestamp: Date.now() / 1000
    };

    this.ws.send(JSON.stringify(message));
  }

  onMessage(data: string) {
    const msg: ServerMessage = JSON.parse(data);

    switch (msg.type) {
      case 'game_state':
        this.handleGameState(msg.payload);
        break;
      case 'error':
        this.handleError(msg.payload);
        break;
      case 'ack':
        this.handleAck(msg.payload);
        break;
    }
  }

  private handleGameState(state: GameState) {
    // TypeScript knows all fields:
    // state.position.fen
    // state.players
    // state.clock
    // etc.
  }
}
```

## File Structure Recommendation

Suggested frontend organization:

```
frontend/ui/modules/games/
├── modules/
│   ├── types.ts                 ← Protocol types (from server)
│   ├── connection.ts            ← Connection config
│   ├── websocket-client.ts      ← Your WS client implementation
│   ├── game-state-manager.ts   ← State management
│   └── __fixtures__/
│       └── sample-messages.json ← Test data
├── components/
│   ├── Board.tsx
│   ├── GameInfo.tsx
│   └── MoveHistory.tsx
└── hooks/
    ├── useGameState.ts
    └── useWebSocket.ts
```

## Syncing Updates

When server protocol changes:

1. Update server files first
2. Re-read `types.py` and `export.py`
3. Manually update `types.ts` to match
4. Update sample messages if needed
5. Update frontend code to handle new fields

## Questions?

- Protocol questions → Check server source
- Type mismatches → Server is correct, update frontend
- Missing fields → Check `export_state()` in `export.py`
- Message format → Check `sample-messages.json` examples

---

**Remember:** Frontend depends on server protocol, not server implementation.
Only sync protocol shapes, never implementation code.
