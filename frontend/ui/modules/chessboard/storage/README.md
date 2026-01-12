# Chessboard Storage

Game storage system that triggers backend to save game state, PGN, and variations.

## Architecture

⚠️ **Important**: Frontend only triggers save events. All logic is in backend.

### Frontend Responsibility
- Trigger save events when moves are made
- Provide UI for comments and annotations
- Display game history

### Backend Responsibility
- Generate PGN with variations (e.g., `1.e4 (1.d4 Nf6)`)
- Handle variation branches
- Store to R2 database
- Manage game state

## Usage

### Basic Auto-Save

```typescript
import { createGameStorage } from './storage';
import { createChessboard } from './chessboard';

// Create storage manager
const storage = createGameStorage({
  autoSave: true,
  gameInfo: {
    gameId: 'game_123',
    playerWhite: 'Player 1',
    playerBlack: 'Player 2',
    event: 'Casual Game',
  },
  onSaved: (gameId) => {
    console.log('Game saved:', gameId);
  },
});

// Create chessboard with storage
const chessboard = createChessboard(container, {
  onMove: async (move) => {
    // Trigger backend to save move
    await storage.saveMove({
      gameId: storage.getGameId()!,
      move: move,
      position: chessboard.getPosition(),
    });
  },
});
```

### Variation Branches

```typescript
// Start a variation branch
// Backend will format as: 1.e4 (1.d4 Nf6 2.c4) e5
await storage.startVariation(parentMoveId);

// Make moves in variation
await storage.saveMove({
  gameId: storage.getGameId()!,
  move: alternativeMove,
  position: chessboard.getPosition(),
  isVariation: true,
  parentMoveId: parentMoveId,
});

// End variation
await storage.endVariation();
```

### Comments and Annotations

```typescript
// Add comment to last move
await storage.addComment('Good move!');

// Add NAG (Numeric Annotation Glyph)
await storage.addNAG(1); // ! (good move)
await storage.addNAG(2); // ? (mistake)
await storage.addNAG(3); // !! (brilliant move)
await storage.addNAG(4); // ?? (blunder)
```

### Get PGN

```typescript
// Get complete PGN from backend
const pgn = await storage.getPGN();
console.log(pgn);

// Example output:
// [Event "Casual Game"]
// [Site "Catachess"]
// [Date "2026.01.12"]
// [Round "1"]
// [White "Player 1"]
// [Black "Player 2"]
// [Result "*"]
//
// 1. e4 (1. d4 Nf6 2. c4) e5 2. Nf3 Nc6 *
```

### Load Existing Game

```typescript
// Load game from backend
const loaded = await storage.loadGame('game_123');

if (loaded) {
  const pgn = await storage.getPGN();
  // Parse and display game...
}
```

## Backend API Endpoints

Frontend calls these endpoints (backend implements the logic):

### Save Move
```
POST /api/games/save-move
{
  "game_id": "game_123",
  "move": {
    "from": { "file": 4, "rank": 1 },
    "to": { "file": 4, "rank": 3 }
  },
  "position_fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
  "is_variation": false,
  "parent_move_id": null,
  "comment": null,
  "nag": null,
  "move_number": 1
}
```

Backend will:
1. Validate move
2. Update game tree with new move
3. Generate updated PGN
4. Store to R2 database
5. Return success

### Start Variation
```
POST /api/games/start-variation
{
  "game_id": "game_123",
  "parent_move_id": "move_5"
}
```

Backend will:
1. Mark current position as variation start point
2. Prepare to record alternative moves
3. Update game tree structure

### End Variation
```
POST /api/games/end-variation
{
  "game_id": "game_123"
}
```

Backend will:
1. Close current variation branch
2. Return to main line
3. Update PGN with variation notation `(1...d5)`

### Add Comment
```
POST /api/games/add-comment
{
  "game_id": "game_123",
  "move_id": "move_5",
  "comment": "Good move!"
}
```

Backend will:
1. Add comment to specified move
2. Update PGN: `5. Nf3 { Good move! }`

### Add NAG
```
POST /api/games/add-nag
{
  "game_id": "game_123",
  "move_id": "move_5",
  "nag": 1
}
```

Backend will:
1. Add NAG to specified move
2. Update PGN: `5. Nf3 !`

### Get PGN
```
GET /api/games/{game_id}/pgn
```

Returns:
```json
{
  "pgn": "[Event \"Casual Game\"]\n[Site \"Catachess\"]...",
  "game_id": "game_123"
}
```

### Load Game
```
GET /api/games/{game_id}
```

Returns:
```json
{
  "game_id": "game_123",
  "pgn": "...",
  "move_count": 42,
  "current_position": "...",
  "player_white": "Player 1",
  "player_black": "Player 2"
}
```

### Delete Game
```
DELETE /api/games/{game_id}
```

Backend will:
1. Delete game from R2
2. Clear all associated data

## NAG Codes

Common NAG (Numeric Annotation Glyph) codes:

| NAG | Symbol | Meaning |
|-----|--------|---------|
| 1   | !      | Good move |
| 2   | ?      | Mistake |
| 3   | !!     | Brilliant move |
| 4   | ??     | Blunder |
| 5   | !?     | Interesting move |
| 6   | ?!     | Dubious move |

## Example: Complete Game with Variations

```typescript
const storage = createGameStorage({
  autoSave: true,
  gameInfo: {
    gameId: 'game_123',
    playerWhite: 'Carlsen',
    playerBlack: 'Nakamura',
    event: 'Speed Chess Championship',
  },
});

// Main line
await storage.saveMove({ /* 1.e4 */ });
await storage.saveMove({ /* 1...e5 */ });
await storage.saveMove({ /* 2.Nf3 */ });

// Start variation
await storage.startVariation('move_2'); // At move 2
await storage.saveMove({ /* 2...d6 */ isVariation: true });
await storage.addComment('Philidor Defense');
await storage.endVariation();

// Continue main line
await storage.saveMove({ /* 2...Nc6 */ });
await storage.addNAG(1); // Good move

// Result PGN:
// 1. e4 e5 2. Nf3 (2...d6 { Philidor Defense }) Nc6 ! 3. Bb5 ...
```

## Integration with R2

Backend stores games in Cloudflare R2:

```
Bucket: catachess-games
Path: /games/{user_id}/{game_id}.pgn
```

Each save triggers:
1. Update in-memory game tree
2. Generate PGN
3. Upload to R2
4. Update database metadata

## Performance

- Frontend: Lightweight event triggers only
- Backend: Efficient PGN generation with `chess_basic.pgn` module
- R2: Fast object storage with CDN
- Auto-save: Debounced to avoid excessive API calls

## Error Handling

```typescript
const storage = createGameStorage({
  onError: (error) => {
    console.error('Storage error:', error);
    // Show user notification
    showNotification('Failed to save game', 'error');
  },
});
```

## Future Enhancements

- [ ] Batch save multiple moves
- [ ] Offline mode with sync
- [ ] Conflict resolution for concurrent edits
- [ ] Compression for large games
- [ ] Export to various formats (PDF, GIF, etc.)
