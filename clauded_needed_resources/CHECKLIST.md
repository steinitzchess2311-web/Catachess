# Integration Checklist

Use this checklist to integrate the protocol files into your frontend.

---

## Phase 1: Copy Files (5 minutes)

### Essential Files (Must Copy)

- [ ] Copy [types.ts](types.ts) to your frontend
  ```bash
  cp types.ts ../frontend/ui/modules/games/modules/types.ts
  ```

- [ ] Copy [connection-config.ts](connection-config.ts)
  ```bash
  cp connection-config.ts ../frontend/ui/modules/games/modules/connection.ts
  ```

### Recommended Files

- [ ] Copy [sample-messages.json](sample-messages.json) for testing
  ```bash
  mkdir -p ../frontend/ui/modules/games/modules/__fixtures__
  cp sample-messages.json ../frontend/ui/modules/games/modules/__fixtures__/
  ```

- [ ] Copy [index.ts](index.ts) for easier imports
  ```bash
  cp index.ts ../frontend/ui/modules/games/modules/index.ts
  ```

### Optional Files

- [ ] Copy [.env.example](.env.example) and customize
  ```bash
  cp .env.example ../frontend/.env.local
  # Edit .env.local with your values
  ```

- [ ] Copy or adapt [websocket-client-example.ts](websocket-client-example.ts)
  ```bash
  cp websocket-client-example.ts ../frontend/ui/modules/games/modules/websocket-client.ts
  ```

---

## Phase 2: Verify Setup (2 minutes)

- [ ] Files are in correct locations
- [ ] No TypeScript errors when importing
- [ ] IDE autocomplete works for types

Quick test:
```typescript
import type { GameState } from './modules/types';
import { WS_BASE } from './modules/connection';

// This should work without errors
const state: GameState = {} as any;
console.log(WS_BASE);
```

---

## Phase 3: Build WebSocket Client (30-60 minutes)

### Option A: Use the example client

- [ ] Import `GameWebSocketClient` from websocket-client-example.ts
- [ ] Create instance with your game/player IDs
- [ ] Set up message handlers
- [ ] Test connection

```typescript
import { GameWebSocketClient } from './modules/websocket-client';

const client = new GameWebSocketClient({
  gameId: 'your-game-id',
  playerId: 'your-player-id',
  onMessage: (msg) => {
    // Handle messages
  }
});

client.connect();
```

### Option B: Build your own client

- [ ] Create WebSocket connection using `WS_BASE`
- [ ] Implement message sending with proper types
- [ ] Implement message receiving with type guards
- [ ] Add reconnection logic
- [ ] Add error handling

---

## Phase 4: Build UI Components (Time varies)

### Game State Display

- [ ] Create component to display `GameState`
- [ ] Show board from `state.position.fen`
- [ ] Show turn from `state.position.turn`
- [ ] Show move history from `state.position.move_history`
- [ ] Show clock if `state.clock` exists

### User Actions

- [ ] Move input component
- [ ] Resign button
- [ ] Draw offer/accept/decline buttons
- [ ] Sync/reconnect button

### Type your components

```typescript
interface GameBoardProps {
  state: GameState;
  onMove: (move: string) => void;
}

function GameBoard({ state, onMove }: GameBoardProps) {
  // state.position.fen
  // state.position.turn
  // etc.
}
```

---

## Phase 5: Testing (Recommended)

### Unit Tests

- [ ] Test message parsing with sample-messages.json
- [ ] Test WebSocket client with mocks
- [ ] Test state updates in components

```typescript
import sampleMessages from './modules/__fixtures__/sample-messages.json';

const mockState = sampleMessages.server_to_client.game_state_active;
// Use in tests
```

### Integration Tests

- [ ] Test connecting to server
- [ ] Test sending moves
- [ ] Test receiving state updates
- [ ] Test error handling
- [ ] Test reconnection

### Manual Testing

- [ ] Can join a game
- [ ] Can make moves
- [ ] State updates work
- [ ] Clock updates work (if enabled)
- [ ] Errors display properly
- [ ] Reconnection works

---

## Phase 6: Polish (Optional)

### Error Handling

- [ ] Display user-friendly error messages
- [ ] Handle connection errors
- [ ] Handle protocol errors (invalid move, etc.)
- [ ] Show loading states

### User Experience

- [ ] Show connection status
- [ ] Show whose turn it is
- [ ] Highlight valid moves
- [ ] Show move history
- [ ] Animate moves
- [ ] Sound effects

### Performance

- [ ] Optimize re-renders
- [ ] Memoize expensive calculations
- [ ] Lazy load components
- [ ] Add loading indicators

---

## Verification Checklist

Before deploying:

- [ ] All types imported correctly
- [ ] No TypeScript errors
- [ ] WebSocket connects successfully
- [ ] Can send and receive messages
- [ ] State updates trigger UI updates
- [ ] Errors are handled gracefully
- [ ] Reconnection works
- [ ] Game is playable end-to-end

---

## Common Issues and Solutions

### Issue: TypeScript can't find types
**Solution:** Check import paths, ensure types.ts is in correct location

### Issue: WebSocket won't connect
**Solution:** Check WS_BASE URL, verify server is running, check CORS

### Issue: Messages not typed correctly
**Solution:** Use type guards, check message.type before accessing payload

### Issue: State not updating
**Solution:** Check message handler is called, verify state management setup

### Issue: Reconnection not working
**Solution:** Check autoReconnect option, verify reconnection logic

---

## Need Help?

- Protocol questions → Check server source files
- Type questions → Check [types.ts](types.ts)
- Example code → Check [websocket-client-example.ts](websocket-client-example.ts)
- Quick reference → Check [QUICK-REFERENCE.md](QUICK-REFERENCE.md)
- Detailed guide → Check [README.md](README.md)

---

## Progress Tracking

Mark your progress:
- Phase 1: ⬜ Not started / 🔄 In progress / ✅ Complete
- Phase 2: ⬜ Not started / 🔄 In progress / ✅ Complete
- Phase 3: ⬜ Not started / 🔄 In progress / ✅ Complete
- Phase 4: ⬜ Not started / 🔄 In progress / ✅ Complete
- Phase 5: ⬜ Not started / 🔄 In progress / ✅ Complete
- Phase 6: ⬜ Not started / 🔄 In progress / ✅ Complete

---

**Ready to start?** → Begin with Phase 1! 🚀
