# Frontend Architecture

Complete frontend system with desktop-style window management and chess functionality.

## Overview

The frontend is built with a modular architecture consisting of:

1. **Core System** - Window management infrastructure
2. **Modules** - Feature-specific components (chessboard, workspace, etc.)
3. **Examples** - Usage demonstrations

## Directory Structure

```
frontend/
└── ui/
    ├── core/                      # Core window management system
    │   ├── pointer/               # Pointer event handling
    │   ├── focus/                 # Z-index and focus management
    │   ├── drag/                  # Drag and drop
    │   ├── resize/                # Element resizing
    │   ├── scroll/                # Smooth scrolling
    │   ├── utils/                 # Snapping and maximize
    │   └── index.ts               # Unified API
    │
    ├── modules/                   # Feature modules
    │   ├── chessboard/            # Chess board component
    │   │   ├── components/        # UI components
    │   │   ├── types/             # Type definitions
    │   │   ├── utils/             # Utilities and API
    │   │   └── index.ts           # Module exports
    │   │
    │   ├── workspace/             # Workspace management
    │   └── signup/                # Authentication
    │
    └── examples/                  # Usage examples
        └── chessboard-example.ts  # Chess panel demo
```

## Core System

The core system provides a complete desktop-style window management solution.

### Key Features

✅ **Pointer Management** - Unified touch/mouse handling
✅ **Focus Management** - Z-index without hell
✅ **Drag & Drop** - Smooth element dragging
✅ **Resize** - 8-direction resize handles
✅ **Scroll** - Smooth animated scrolling
✅ **Window Snapping** - macOS-style edge snapping
✅ **Maximize/Restore** - Window state management

### Usage

```typescript
import { createPanel } from './ui/core';

const panel = createPanel({
  id: 'my-panel',
  element: element,
  draggable: true,
  resizable: true,
  focusable: true,
  snapEnabled: true,
});
```

See [core/README.md](./ui/core/README.md) for detailed documentation.

## Chessboard Module

Interactive chess board with backend integration.

### Features

- ✅ Drag-and-drop piece movement
- ✅ Click-to-select and move
- ✅ Legal move highlighting
- ✅ Backend move validation
- ✅ Board orientation flip
- ✅ Coordinate display
- ✅ Move history

### Usage

```typescript
import { createChessboard } from './ui/modules/chessboard';

const chessboard = createChessboard(container, {
  draggable: true,
  showLegalMoves: true,
  onMove: (move) => {
    console.log('Move:', move);
  },
});
```

See [modules/chessboard/README.md](./ui/modules/chessboard/README.md) for detailed documentation.

## Integration Example

Combining core window management with chessboard:

```typescript
import { createPanel } from './ui/core';
import { createChessboard } from './ui/modules/chessboard';

// Create draggable, resizable, snappable panel
const panelElement = document.createElement('div');
panelElement.style.cssText = `
  position: absolute;
  width: 600px;
  height: 700px;
  background: white;
  border-radius: 8px;
`;

document.body.appendChild(panelElement);

// Setup window management
const panel = createPanel({
  id: 'chess-panel',
  element: panelElement,
  draggable: true,
  resizable: true,
  focusable: true,
  snapEnabled: true,
  dragHandle: '.header',
  minWidth: 400,
  minHeight: 500,
});

// Add chessboard to panel
const boardContainer = document.createElement('div');
panelElement.appendChild(boardContainer);

const chessboard = createChessboard(boardContainer, {
  draggable: true,
  showCoordinates: true,
  showLegalMoves: true,
});

// Panel controls
panel.focus();              // Bring to front
panel.maximize();           // Maximize
panel.restore();            // Restore
panel.toggleMaximize();     // Toggle

// Board controls
chessboard.flip();          // Flip orientation
chessboard.reset();         // Reset position
```

## Backend Integration

The frontend communicates with the backend via REST API.

### Chess API Endpoints

```
POST /api/chess/validate-move    - Validate move legality
POST /api/chess/legal-moves      - Get all legal moves
POST /api/chess/apply-move       - Apply move and get new position
POST /api/chess/is-check         - Check if in check
POST /api/chess/is-checkmate     - Check if checkmate
```

### Example Request

```typescript
// Validate move
const isValid = await chessAPI.validateMove(position, move);

// Get legal moves
const moves = await chessAPI.getLegalMoves(position, square);

// Apply move
const newPosition = await chessAPI.applyMove(position, move);
```

## Design Principles

### Modularity
Each module is self-contained and can be used independently.

### Composability
Modules can be combined to create complex interfaces.

### Type Safety
Full TypeScript support with comprehensive type definitions.

### Performance
- Efficient event handling
- Minimal DOM manipulation
- RequestAnimationFrame for animations
- Event delegation

### Extensibility
Easy to add new modules and extend existing ones.

## State Management

### Core System State
- Pointer state (position, dragging)
- Focus order (z-index management)
- Window states (maximized, snapped)
- Drag/resize state

### Module State
Each module manages its own state independently.

Example (Chessboard):
```typescript
interface ChessboardState {
  position: BoardPosition;
  selectedSquare: Square | null;
  legalMoves: Move[];
  highlightedSquares: Square[];
  lastMove: Move | null;
  isFlipped: boolean;
}
```

## Event System

### Pointer Events
```typescript
pointerManager.on('down', callback);
pointerManager.on('move', callback);
pointerManager.on('up', callback);
```

### Focus Events
```typescript
focusManager.onFocusChange(callback);
```

### Module Events
```typescript
chessboard.onMove(callback);
chessboard.onPieceSelect(callback);
chessboard.onSquareClick(callback);
```

## Styling

### CSS Architecture

Each module provides its own styles:

```typescript
// Core styles are injected automatically
const style = document.createElement('style');
style.textContent = `...`;
document.head.appendChild(style);
```

### Customization

Override CSS classes to customize appearance:

```css
.square.light { background: #f0d9b5; }
.square.dark { background: #b58863; }
.square.selected { background: #9bc700; }
```

## Testing

### Unit Tests
Test individual modules in isolation.

### Integration Tests
Test module interactions and core system.

### E2E Tests
Test complete user workflows.

## Development

### Prerequisites
- Node.js 18+
- TypeScript 5+
- Modern browser

### Setup

```bash
cd frontend
npm install
npm run dev
```

### Build

```bash
npm run build
```

## Roadmap

### Core System
- [x] Pointer management
- [x] Focus management
- [x] Drag and drop
- [x] Resize
- [x] Scroll
- [x] Window snapping
- [x] Maximize/restore
- [ ] Minimize (taskbar)
- [ ] Multiple monitor support
- [ ] Keyboard shortcuts

### Chessboard
- [x] Basic board rendering
- [x] Drag and drop
- [x] Move validation
- [x] Backend integration
- [ ] Chess piece SVGs
- [ ] Move animation
- [ ] Sound effects
- [ ] Promotion dialog
- [ ] Pre-move
- [ ] Analysis arrows
- [ ] Puzzle mode

### New Modules
- [ ] PGN viewer
- [ ] Analysis board
- [ ] Opening explorer
- [ ] Study creator
- [ ] Game database

## Contributing

1. Follow existing code structure
2. Add TypeScript types for all APIs
3. Include documentation
4. Write tests
5. Follow naming conventions

## License

MIT
