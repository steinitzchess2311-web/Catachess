# Chessboard Module

Complete chessboard component with drag-and-drop, move validation, and backend integration.

## Important Note

⚠️ **All chess rules and move validation are handled by the backend Python engine** (`backend/core/chess_basic`).

The frontend is **only responsible for UI interactions**:
- Rendering the board
- Dragging pieces (using `core/pointer` system)
- Visual feedback (highlighting, animations)
- Sending moves to backend for validation

## Features

- 🎯 **Interactive Board**: Click-to-move and drag-and-drop support
- 🖱️ **Advanced Dragging**: Uses core pointer system for smooth piece movement
- ✅ **Move Validation**: All moves validated by backend chess engine
- 🎨 **Visual Feedback**: Legal move highlighting, last move indicator
- 🔄 **Board Orientation**: Flip board to play as white or black
- 📍 **Coordinates**: Optional file/rank labels
- 🎮 **Backend Integration**: Communicates with Python chess engine via REST API

## Installation

```typescript
import { createChessboard } from './ui/modules/chessboard';

const container = document.getElementById('board');
const chessboard = createChessboard(container, {
  orientation: 'white',
  draggable: true,
  showLegalMoves: true,
  onMove: (move) => {
    console.log('Move made:', move);
  },
});
```

## Usage with Core Window Management

Integrate chessboard with the core window management system:

```typescript
import { createPanel } from './ui/core';
import { createChessboard } from './ui/modules/chessboard';

// Create a draggable, resizable panel
const panelElement = document.createElement('div');
panelElement.style.cssText = `
  position: absolute;
  width: 600px;
  height: 650px;
  background: white;
  border: 1px solid #ccc;
  border-radius: 8px;
  overflow: hidden;
`;

document.body.appendChild(panelElement);

// Create panel with window management
const panel = createPanel({
  id: 'chessboard-panel',
  element: panelElement,
  draggable: true,
  resizable: true,
  focusable: true,
  snapEnabled: true,
  dragHandle: '.panel-header',
  minWidth: 400,
  minHeight: 450,
});

// Add header
const header = document.createElement('div');
header.className = 'panel-header';
header.innerHTML = `
  <h3>Chess Board</h3>
  <button onclick="panel.toggleMaximize()">Maximize</button>
`;
panelElement.appendChild(header);

// Create chessboard in panel
const boardContainer = document.createElement('div');
boardContainer.style.cssText = `
  width: 100%;
  height: calc(100% - 50px);
  padding: 10px;
`;
panelElement.appendChild(boardContainer);

const chessboard = createChessboard(boardContainer, {
  draggable: true,
  showCoordinates: true,
  showLegalMoves: true,
  onMove: async (move) => {
    console.log('Move:', move);
    // Handle move...
  },
});
```

## API Reference

### Chessboard Options

```typescript
interface ChessboardOptions {
  initialPosition?: BoardPosition;     // Starting position (default: standard)
  orientation?: 'white' | 'black';     // Board orientation
  draggable?: boolean;                 // Enable drag-and-drop
  selectable?: boolean;                // Enable click-to-select
  showCoordinates?: boolean;           // Show file/rank labels
  showLegalMoves?: boolean;            // Highlight legal moves
  highlightLastMove?: boolean;         // Highlight last move
  onMove?: (move: Move) => void;       // Move callback
  onPieceSelect?: (square: Square, piece: Piece) => void;
  onSquareClick?: (square: Square) => void;
  validateMove?: (move: Move) => Promise<boolean>;
}
```

### Chessboard Methods

```typescript
// Flip board orientation
chessboard.flip();

// Set position
chessboard.setPosition(position);

// Get current position
const position = chessboard.getPosition();

// Reset to initial position
chessboard.reset();

// Destroy and cleanup
chessboard.destroy();
```

## Backend Integration

The chessboard communicates with the backend chess engine via REST API:

### Endpoints

- `POST /api/chess/validate-move` - Validate if a move is legal
- `POST /api/chess/legal-moves` - Get all legal moves
- `POST /api/chess/apply-move` - Apply move and get new position
- `POST /api/chess/is-check` - Check if position is in check
- `POST /api/chess/is-checkmate` - Check if position is checkmate

### Example Backend Request

```json
POST /api/chess/validate-move
{
  "position": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
  "move": {
    "from_square": { "file": 4, "rank": 1 },
    "to_square": { "file": 4, "rank": 3 }
  }
}
```

## Styling

The chessboard uses CSS for styling. You can customize the appearance by overriding the CSS classes:

```css
.square.light {
  background: #f0d9b5;
}

.square.dark {
  background: #b58863;
}

.square.selected {
  background: #9bc700;
}

.piece {
  font-size: 3em;
  /* Add custom piece styling */
}
```

## TODO

- [ ] Add chess piece SVG sprites
- [ ] Implement piece animation
- [ ] Add sound effects for moves
- [ ] Implement promotion dialog
- [ ] Add move history panel
- [ ] Add analysis arrows
- [ ] Add pre-move capability
- [ ] Add puzzle mode
