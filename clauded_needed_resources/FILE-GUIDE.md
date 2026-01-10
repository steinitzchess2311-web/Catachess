# File Guide - What Each File Does

Quick overview of all files in this directory.

---

## 📋 Core Protocol Files (Copy These First)

### 1. [types.ts](types.ts) - ⭐⭐⭐ CRITICAL
**Size:** 6.2 KB
**Purpose:** TypeScript type definitions for WebSocket protocol
**Source:** Mirrored from `types.py` + `export.py`

**Contains:**
- All message types (join, move, game_state, error, etc.)
- `GameState` interface (complete game state structure)
- `PositionState` interface (board, FEN, moves, turn)
- Type-safe message unions

**Use this for:**
- Type safety in your WebSocket client
- Type annotations in components
- IntelliSense/autocomplete in IDE

```typescript
import type { GameState, ServerMessage } from './types';
```

---

### 2. [connection-config.ts](connection-config.ts) - ⭐⭐ IMPORTANT
**Size:** 2.4 KB
**Purpose:** Server endpoints and WebSocket configuration

**Contains:**
- `API_BASE` = "https://iloveliquanhao.catachess.com"
- `WS_BASE` = "wss://iloveliquanhao.catachess.com/ws"
- WebSocket config (reconnect, heartbeat settings)
- Environment override helpers

**Use this for:**
- Connecting to server
- WebSocket reconnection logic
- Heartbeat configuration

```typescript
import { WS_BASE, WS_CONFIG } from './connection-config';
```

---

### 3. [sample-messages.json](sample-messages.json) - ⭐ HELPFUL
**Size:** 6.7 KB
**Purpose:** Real WebSocket message examples

**Contains:**
- Examples of every message type
- Game states at different stages (waiting, active, ended)
- Error examples with different codes
- Realistic FEN strings and move history

**Use this for:**
- Testing UI components
- Mock data in development
- Understanding message structure
- Storybook examples

```typescript
import sampleMessages from './sample-messages.json';
const mockState = sampleMessages.server_to_client.game_state_active;
```

---

## 🔧 Utility Files (Optional But Recommended)

### 4. [index.ts](index.ts)
**Size:** 2.0 KB
**Purpose:** Single entry point for imports

**Re-exports everything from:**
- types.ts
- connection-config.ts

**Use this for:**
- Cleaner imports
- Single import statement

```typescript
// Instead of multiple imports:
import type { GameState } from './types';
import { WS_BASE } from './connection-config';

// Use single import:
import type { GameState } from './index';
import { WS_BASE } from './index';
```

---

### 5. [websocket-client-example.ts](websocket-client-example.ts)
**Size:** 12 KB
**Purpose:** Reference implementation of WebSocket client

**Contains:**
- Complete `GameWebSocketClient` class
- Reconnection logic
- Heartbeat implementation
- Message sending methods
- React hook example
- Full TypeScript types

**Use this for:**
- Understanding how to use the protocol
- Starting point for your own client
- Reference for best practices
- Copy-paste if you want

```typescript
import { GameWebSocketClient } from './websocket-client-example';

const client = new GameWebSocketClient({
  gameId: 'game_abc',
  playerId: 'player_xyz',
  onMessage: (msg) => { /* handle */ }
});
```

---

### 6. [.env.example](.env.example)
**Size:** 1.3 KB
**Purpose:** Environment variable template

**Contains:**
- Server endpoint environment variables
- Development vs production configs
- Debug flags

**Use this for:**
- Creating your `.env.local` file
- Understanding configurable values

```bash
cp .env.example .env.local
# Edit .env.local with your values
```

---

## 📚 Documentation Files (Read These)

### 7. [README.md](README.md)
**Size:** 5.4 KB
**Purpose:** Detailed documentation and explanation

**Read this for:**
- Understanding what was transferred and why
- Integration instructions
- Important principles
- Type safety examples
- File structure recommendations

---

### 8. [QUICK-REFERENCE.md](QUICK-REFERENCE.md)
**Size:** 5.8 KB
**Purpose:** Fast-start guide and common patterns

**Read this for:**
- 1-minute integration guide
- Key type exports list
- GameState structure reference
- Message flow diagrams
- Common code patterns
- React hook examples

---

### 9. [TRANSFER-SUMMARY.md](TRANSFER-SUMMARY.md)
**Size:** 6.1 KB
**Purpose:** What was synced and validation report

**Read this for:**
- Complete list of what was transferred
- Server → Frontend mapping
- Type coverage checklist
- Next steps
- Maintenance instructions

---

### 10. [FILE-GUIDE.md](FILE-GUIDE.md) ← You Are Here
**Size:** This file
**Purpose:** Quick overview of all files

---

## 🚀 Quick Start Checklist

### Minimum Integration (5 minutes):
```bash
# 1. Copy essential files
cp types.ts frontend/ui/modules/games/modules/
cp connection-config.ts frontend/ui/modules/games/modules/

# 2. Import in your code
# See types.ts for usage
```

### Recommended Integration (10 minutes):
```bash
# 1. Copy core files
cp types.ts frontend/ui/modules/games/modules/
cp connection-config.ts frontend/ui/modules/games/modules/
cp index.ts frontend/ui/modules/games/modules/

# 2. Copy test data
mkdir -p frontend/ui/modules/games/modules/__fixtures__
cp sample-messages.json frontend/ui/modules/games/modules/__fixtures__/

# 3. Set up environment
cp .env.example .env.local
# Edit .env.local if needed
```

### Full Integration (20 minutes):
```bash
# Do recommended integration first, then:

# 4. Use or adapt the example client
cp websocket-client-example.ts frontend/ui/modules/games/modules/

# 5. Read documentation
# - Start with QUICK-REFERENCE.md for fast start
# - Read README.md for detailed explanation
# - Check TRANSFER-SUMMARY.md for what was synced
```

---

## 📊 File Import Priority

**Must have:**
1. types.ts
2. connection-config.ts

**Should have:**
3. sample-messages.json
4. index.ts

**Nice to have:**
5. websocket-client-example.ts
6. .env.example

**Documentation:**
7. QUICK-REFERENCE.md (read first)
8. README.md (read for details)
9. TRANSFER-SUMMARY.md (reference)

---

## 🎯 Use Case → File Mapping

| I want to... | Use this file |
|-------------|---------------|
| Type my WebSocket messages | types.ts |
| Connect to server | connection-config.ts |
| Mock data for testing | sample-messages.json |
| Build a WebSocket client | websocket-client-example.ts |
| Quick start guide | QUICK-REFERENCE.md |
| Understand the protocol | README.md |
| See what was synced | TRANSFER-SUMMARY.md |
| Configure environment | .env.example |
| Single import point | index.ts |

---

## 📦 File Dependencies

```
index.ts
├── types.ts (re-exports)
└── connection-config.ts (re-exports)

websocket-client-example.ts
├── types.ts (imports)
└── connection-config.ts (imports)

Your code should import from:
├── index.ts (recommended)
└── Or individual files (also fine)
```

---

## 🔄 Maintenance

When server protocol changes:

1. Update server files (types.py, export.py)
2. Re-read those files
3. Update types.ts to match
4. Update sample-messages.json if needed
5. Update your frontend code

---

## ❓ Which File Should I Read First?

**If you want to:**
- Start coding immediately → QUICK-REFERENCE.md
- Understand deeply → README.md
- See what's included → TRANSFER-SUMMARY.md
- Find a specific file → FILE-GUIDE.md (this file)

**For coding:**
- Check types.ts for type definitions
- Check sample-messages.json for examples
- Check websocket-client-example.ts for implementation

---

## Summary Table

| File | Size | Type | Priority | Purpose |
|------|------|------|----------|---------|
| types.ts | 6.2 KB | Code | ⭐⭐⭐ | Protocol types |
| connection-config.ts | 2.4 KB | Code | ⭐⭐ | Server endpoints |
| sample-messages.json | 6.7 KB | Data | ⭐ | Test data |
| index.ts | 2.0 KB | Code | ⭐ | Export hub |
| websocket-client-example.ts | 12 KB | Code | Optional | Reference impl |
| .env.example | 1.3 KB | Config | Optional | Env template |
| README.md | 5.4 KB | Docs | Read | Full guide |
| QUICK-REFERENCE.md | 5.8 KB | Docs | Read | Quick start |
| TRANSFER-SUMMARY.md | 6.1 KB | Docs | Reference | Sync report |
| FILE-GUIDE.md | This | Docs | Reference | File overview |

**Total size:** ~48 KB (excluding docs)

---

**Status:** ✅ All files ready for frontend integration
