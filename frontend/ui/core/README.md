# Frontend Core System

Complete desktop-style window management system with drag, resize, focus, and snap capabilities.

## Architecture

```
frontend/ui/core/
├── pointer/        # Unified pointer event handling
├── focus/          # Z-index and focus management
├── drag/           # Element dragging
├── resize/         # Element resizing
├── scroll/         # Smooth scrolling
├── utils/          # Window snapping & maximize
└── index.ts        # Unified API
```

## Features

### 🎯 Pointer Management
- Unified touch/mouse event handling
- Pointer capture and tracking
- Distance and delta calculations

### 🎨 Focus Management
- Automatic z-index management (no z-index hell!)
- Click-to-focus behavior
- Focus order tracking
- Bring to front / send to back

### 🖱️ Drag & Drop
- Smooth element dragging
- Grid snapping
- Viewport/parent constraints
- Axis locking
- Custom drag handles

### 📐 Resize
- 8-direction resize handles
- Min/max size constraints
- Aspect ratio locking
- Grid snapping

### 📜 Scroll
- Smooth scroll animations
- Easing functions
- Scroll position tracking
- Scroll into view

### 🪟 Window Management
- Edge snapping (macOS-style)
- Maximize/restore
- Window state tracking
- Snap zones (left, right, top, bottom, corners)

## Quick Start

### Basic Panel

```typescript
import { createPanel } from './ui/core';

const element = document.getElementById('my-panel');

const panel = createPanel({
  id: 'panel-1',
  element: element,
  draggable: true,
  resizable: true,
  focusable: true,
  snapEnabled: true,
  dragHandle: '.header',
  minWidth: 300,
  minHeight: 200,
});

// Focus panel
panel.focus();

// Maximize panel
panel.maximize();

// Restore panel
panel.restore();
```

### Manual Control

```typescript
import {
  makeDraggable,
  makeResizable,
  focusManager,
  snapManager,
  windowStateManager,
} from './ui/core';

// Make element draggable
const draggable = makeDraggable(element, {
  handle: '.drag-handle',
  constrainToViewport: true,
  grid: 10,
});

// Make element resizable
const resizable = makeResizable(element, {
  minWidth: 200,
  minHeight: 150,
  aspectRatio: 16/9,
});

// Register for focus management
const unsubscribe = focusManager.register('my-element', element);

// Handle snapping
element.addEventListener('drag', (e) => {
  const zone = snapManager.detectSnapZone(e.clientX, e.clientY);
  if (zone) {
    snapManager.showSnapPreview(zone);
  }
});
```

## Modules

### Pointer Module

Unified pointer event handling with touch/mouse support.

```typescript
import { pointerManager } from './ui/core/pointer';

pointerManager.on('down', (data) => {
  console.log('Pointer down:', data.position);
});

pointerManager.on('move', (data) => {
  console.log('Pointer move:', data.position);
});

pointerManager.on('up', (data) => {
  console.log('Pointer up:', data.position);
});
```

### Focus Module

Z-index and focus order management without z-index hell.

```typescript
import { focusManager } from './ui/core/focus';

// Register elements
focusManager.register('window-1', element1);
focusManager.register('window-2', element2);

// Focus element (brings to front)
focusManager.focus('window-1');

// Get focus order
const order = focusManager.getFocusOrder();

// Listen to focus changes
focusManager.onFocusChange((focusedId) => {
  console.log('Focused:', focusedId);
});
```

### Drag Module

Element dragging with constraints and snapping.

```typescript
import { makeDraggable } from './ui/core/drag';

const draggable = makeDraggable(element, {
  handle: '.drag-handle',
  constrainToViewport: true,
  grid: 20,
  axis: 'both',
  onDragStart: (el, pos) => {
    console.log('Drag start:', pos);
  },
  onDrag: (el, pos) => {
    console.log('Dragging:', pos);
  },
  onDragEnd: (el, pos) => {
    console.log('Drag end:', pos);
  },
});

// Control programmatically
draggable.setPosition(100, 100);
draggable.disable();
draggable.enable();
```

### Resize Module

Element resizing with handles and constraints.

```typescript
import { makeResizable } from './ui/core/resize';

const resizable = makeResizable(element, {
  handles: ['n', 's', 'e', 'w', 'ne', 'nw', 'se', 'sw'],
  minWidth: 200,
  minHeight: 150,
  maxWidth: 1000,
  maxHeight: 800,
  aspectRatio: 16/9,
  grid: 10,
  onResize: (el, size) => {
    console.log('Resizing:', size);
  },
});
```

### Scroll Module

Smooth scrolling with animations.

```typescript
import { createScrollController } from './ui/core/scroll';

const scroll = createScrollController(element);

// Smooth scroll to position
await scroll.scrollTo(0, 500, {
  duration: 300,
  easing: easings.easeInOutQuad,
});

// Scroll by delta
await scroll.scrollBy(0, 100);

// Scroll to top/bottom
await scroll.scrollToTop();
await scroll.scrollToBottom();

// Listen to scroll events
scroll.onScroll((position) => {
  console.log('Scroll:', position);
});
```

### Utils Module

Window snapping and maximize utilities.

```typescript
import { snapManager, windowStateManager } from './ui/core/utils';

// Detect snap zone
const zone = snapManager.detectSnapZone(x, y);

// Show snap preview
if (zone) {
  snapManager.showSnapPreview(zone);
}

// Maximize window
windowStateManager.maximize('window-1', element);

// Restore window
windowStateManager.restore('window-1', element);

// Toggle maximize
windowStateManager.toggleMaximize('window-1', element);

// Snap to zone
windowStateManager.snap('window-1', element, zone);
```

## Snap Zones

The system supports macOS-style window snapping:

- **Left Edge**: Snap to left half
- **Right Edge**: Snap to right half
- **Top Edge**: Maximize
- **Top-Left Corner**: Snap to top-left quarter
- **Top-Right Corner**: Snap to top-right quarter
- **Bottom-Left Corner**: Snap to bottom-left quarter
- **Bottom-Right Corner**: Snap to bottom-right quarter

## Integration with Other Modules

### Chessboard Example

```typescript
import { createPanel } from './ui/core';
import { createChessboard } from './ui/modules/chessboard';

// Create panel
const panel = createPanel({
  id: 'chess-panel',
  element: panelElement,
  draggable: true,
  resizable: true,
  snapEnabled: true,
});

// Create chessboard inside panel
const chessboard = createChessboard(boardContainer, {
  draggable: true,
  showLegalMoves: true,
});
```

## Browser Support

- Chrome/Edge 89+
- Firefox 87+
- Safari 14+
- Modern mobile browsers

## Performance

- Uses pointer events for unified touch/mouse handling
- Efficient z-index management (no style recalculations)
- RequestAnimationFrame for smooth animations
- Event delegation where possible

## License

MIT
