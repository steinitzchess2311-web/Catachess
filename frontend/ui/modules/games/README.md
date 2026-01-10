# CataChess Game Module

Professional, modular chess game frontend with WebSocket integration.

## 📁 Directory Structure

```
games/
├── README.md                        # This file
├── STRUCTURE.md                     # Detailed structure notes
├── skeleton/                        # Pure layout reference (no functionality)
│   ├── skeleton.html                # Single-file skeleton with inline CSS
│   └── README.md                    # Skeleton documentation
├── modules/                         # Functional TypeScript modules
│   ├── core/                        # Core functionality
│   │   ├── config.ts                # Server connection config
│   │   ├── types.ts                 # Protocol types (from server)
│   │   ├── ws.ts                    # WebSocket client
│   │   └── state.ts                 # State management
│   ├── ui/                          # UI coordination
│   │   ├── index.ts                 # Main entry point
│   │   ├── renderer.ts              # Main renderer coordinator
│   │   └── events.ts                # Event handlers
│   └── renderers/                   # Region-specific renderers
│       ├── info.ts                  # Game meta & player info renderer
│       ├── clock.ts                 # Chess clock renderer
│       ├── history.ts               # Move history renderer
│       ├── board.ts                 # Chess board renderer
│       ├── chat.ts                  # Chat messages renderer
│       └── actions.ts               # Action buttons renderer
└── assets/
    └── photos/                      # Assets directory (empty)
```

## 🎨 Layout Regions (Skeleton IDs)

The skeleton defines the DOM IDs used by renderers/events:

**Header**
- `#app-frame`, `#header`
- `#left-long-bar`, `#button-b1` ~ `#button-b4`, `#search-box`, `#right-small-box`

**Left Column**
- `#game-meta`, `#player-info`
- `#chat-title-bar`, `#chat-messages`, `#chat-input-area`

**Center**
- `#chess-board`

**Right Column**
- `#clock-white`, `#clock-black`
- `#move-history-list`
- `#action-resign`, `#action-draw`, `#action-takeback`, `#action-extra`

**Bottom**
- `#bottom-long-bar`

## 🚀 Quick Start

### View Skeleton Only

```bash
cd frontend/ui/modules/games/skeleton
python3 -m http.server 7999
# Open: http://localhost:7999/skeleton.html
```

### Runtime Entry (WIP)

There is no bundled runtime HTML yet. Create an `index.html` that loads the compiled JS for `modules/ui/index.ts`, or add a build step that outputs a browser-ready bundle.

## 📦 Module Overview

### Core Modules (`modules/core/`)

**config.ts** - Server configuration
- `WS_BASE` - WebSocket endpoint
- `API_BASE` - HTTP API endpoint
- `WS_CONFIG` - Connection settings

**types.ts** - Protocol types (READ-ONLY, mirrors server)
- `GameState` - Complete game state
- `ServerMessage` - Server → Client messages
- `ClientMessage` - Client → Server messages

**ws.ts** - WebSocket client
- Auto-reconnection (exponential backoff)
- Heartbeat/ping mechanism
- Sequence tracking
- Methods: `connect()`, `move()`, `resign()`, `offerDraw()`, etc.

**state.ts** - State management
- Observable pattern
- `gameStateManager` singleton
- Subscribe to game/connection state changes

### UI Modules (`modules/ui/`)

**renderer.ts** - Main coordinator
- Delegates to region-specific renderers
- `render(state)` - Update all regions

**events.ts** - Event handling
- Action button handlers
- Board click handlers (placeholder)
- Keyboard shortcuts

**index.ts** - Main entry point
- `GameApp` class - Application controller
- Auto-initialization from URL params
- Coordinates all modules

### Region Renderers (`modules/renderers/`)

- `info.ts` - Game meta + player info
- `clock.ts` - Chess clocks (White/Black)
- `history.ts` - Move history list
- `board.ts` - Chess board (placeholder)
- `chat.ts` - Chat messages
- `actions.ts` - Action button states

## 🎯 Architecture

```
┌─────────────────────────────────────────┐
│           index.ts (GameApp)            │
│         Main Controller                 │
└──────────┬────────────┬─────────────────┘
           │            │
    ┌──────▼─────┐  ┌──▼──────────┐
    │ WebSocket  │  │  State      │
    │  Client    │  │  Manager    │
    └──────┬─────┘  └──┬──────────┘
           │           │
    ┌──────▼───────────▼─────┐
    │     UI Renderer         │
    │    (Coordinator)        │
    └──────┬──────────────────┘
           │
    ┌──────▼──────────────────┐
    │  Region Renderers       │
    │  ├── info.ts            │
    │  ├── clock.ts           │
    │  ├── history.ts         │
    │  ├── board.ts           │
    │  ├── chat.ts            │
    │  └── actions.ts         │
    └─────────────────────────┘
```

## 📡 WebSocket Protocol

### Client → Server

```typescript
{
  type: 'join' | 'move' | 'resign' | 'draw_offer',
  game_id: string,
  player_id: string,
  seq: number,
  payload: { ... },
  timestamp: number
}
```

### Server → Client

```typescript
{
  type: 'game_state' | 'error' | 'ack',
  game_id: string,
  player_id: string,
  seq: number,
  payload: { ... },
  timestamp: number
}
```

### Game State Structure

```typescript
{
  game_id: string,
  state: 'waiting' | 'active' | 'ended',
  players: { [player_id]: { color, player_id } },
  position: {
    turn: 'white' | 'black',
    move_number: number,
    move_history: string[],
    fen: string,
    result: 'in_progress' | 'white_wins' | 'black_wins' | 'draw'
  },
  clock?: { white: number, black: number }
}
```

## 🛠️ Development

### Adding a New Feature

1. **UI Reference** - Update `skeleton/skeleton.html` (layout reference only)
2. **Renderer** - Create/update region renderer in `modules/renderers/`
3. **Events** - Add event handlers in `modules/ui/events.ts`
4. **Protocol** - Update `modules/core/types.ts` (if server changed)

### File Size Constraint

**All files must be ≤ 100 lines**. If a file exceeds 100 lines:
1. Split by function/responsibility
2. Create a directory for related modules
3. Create an index file to combine them

Example: `renderer.ts` was split into 6 region renderers + coordinator.

## 🎨 Styling

**Current:** Inline skeleton CSS in `skeleton/skeleton.html` (positioning only).

**Future Options:**
1. Extract the skeleton styles into a shared CSS file
2. Add theme/style CSS layered on top of the skeleton positions
3. Add classes dynamically via JavaScript renderers

## 🧪 Testing

See `frontend/tests/` for:
- Type validation tests
- WebSocket mock tests
- Test runner (browser-based)

## 📝 Notes

### Protocol Types

`modules/core/types.ts` is a READ-ONLY mirror of server types. Never modify without updating the server first. Server is the source of truth.

### Board Rendering

Currently shows FEN string. Replace `modules/renderers/board.ts` with actual chess board implementation (64 squares, pieces, drag-drop, etc.).

### Chat System

Chat is placeholder. Implement in `modules/renderers/chat.ts` and `modules/ui/events.ts`.

## 🔗 Resources

- Server connection: `wss://iloveliquanhao.catachess.com/ws`
- Protocol docs: `clauded_needed_resources/README.md`
- Sample messages: `frontend/tests/sample-messages.json`
- Tests: `frontend/tests/test_runner.html`

## 📄 License

Part of the CataChess project.
