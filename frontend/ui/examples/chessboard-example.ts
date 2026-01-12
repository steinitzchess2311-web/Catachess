/**
 * Chessboard Example
 *
 * Demonstrates how to use the chessboard module with the core window management system.
 */

import { createPanel } from '../core';
import { createChessboard } from '../modules/chessboard';
import type { Move } from '../modules/chessboard';

/**
 * Create a chess panel with full window management
 */
export function createChessPanel(): void {
  // Create panel container
  const panelElement = document.createElement('div');
  panelElement.className = 'chess-panel';
  panelElement.style.cssText = `
    position: absolute;
    left: 50px;
    top: 50px;
    width: 600px;
    height: 700px;
    background: white;
    border: 1px solid #ccc;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    overflow: hidden;
    display: flex;
    flex-direction: column;
  `;

  document.body.appendChild(panelElement);

  // Create panel header (drag handle)
  const header = document.createElement('div');
  header.className = 'panel-header';
  header.style.cssText = `
    padding: 12px 16px;
    background: #2c3e50;
    color: white;
    display: flex;
    justify-content: space-between;
    align-items: center;
    cursor: move;
    user-select: none;
  `;

  const title = document.createElement('h3');
  title.textContent = 'Chess Board';
  title.style.margin = '0';
  title.style.fontSize = '16px';

  const controls = document.createElement('div');
  controls.style.cssText = 'display: flex; gap: 8px;';

  // Flip button
  const flipBtn = document.createElement('button');
  flipBtn.textContent = '🔄 Flip';
  flipBtn.style.cssText = `
    padding: 4px 12px;
    background: #34495e;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  `;

  // Reset button
  const resetBtn = document.createElement('button');
  resetBtn.textContent = '↺ Reset';
  resetBtn.style.cssText = `
    padding: 4px 12px;
    background: #34495e;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  `;

  // Maximize button
  const maxBtn = document.createElement('button');
  maxBtn.textContent = '⛶';
  maxBtn.style.cssText = `
    padding: 4px 12px;
    background: #34495e;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 16px;
  `;

  // Close button
  const closeBtn = document.createElement('button');
  closeBtn.textContent = '×';
  closeBtn.style.cssText = `
    padding: 4px 12px;
    background: #e74c3c;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 18px;
    font-weight: bold;
  `;

  controls.appendChild(flipBtn);
  controls.appendChild(resetBtn);
  controls.appendChild(maxBtn);
  controls.appendChild(closeBtn);

  header.appendChild(title);
  header.appendChild(controls);
  panelElement.appendChild(header);

  // Create info bar
  const infoBar = document.createElement('div');
  infoBar.className = 'info-bar';
  infoBar.style.cssText = `
    padding: 8px 16px;
    background: #ecf0f1;
    border-bottom: 1px solid #bdc3c7;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 14px;
  `;

  const turnIndicator = document.createElement('span');
  turnIndicator.textContent = "White's turn";
  turnIndicator.style.fontWeight = 'bold';

  const moveCounter = document.createElement('span');
  moveCounter.textContent = 'Move: 1';

  infoBar.appendChild(turnIndicator);
  infoBar.appendChild(moveCounter);
  panelElement.appendChild(infoBar);

  // Create board container
  const boardContainer = document.createElement('div');
  boardContainer.className = 'board-container';
  boardContainer.style.cssText = `
    flex: 1;
    padding: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #34495e;
  `;

  panelElement.appendChild(boardContainer);

  // Create move log
  const moveLog = document.createElement('div');
  moveLog.className = 'move-log';
  moveLog.style.cssText = `
    height: 150px;
    padding: 12px;
    background: #f8f9fa;
    border-top: 1px solid #dee2e6;
    overflow-y: auto;
    font-family: monospace;
    font-size: 12px;
  `;

  const moveLogTitle = document.createElement('div');
  moveLogTitle.textContent = 'Move History';
  moveLogTitle.style.cssText = 'font-weight: bold; margin-bottom: 8px;';
  moveLog.appendChild(moveLogTitle);

  const moveList = document.createElement('div');
  moveList.className = 'move-list';
  moveLog.appendChild(moveList);

  panelElement.appendChild(moveLog);

  // Initialize panel with core window management
  const panel = createPanel({
    id: 'chess-panel-1',
    element: panelElement,
    draggable: true,
    resizable: true,
    focusable: true,
    snapEnabled: true,
    dragHandle: header,
    minWidth: 400,
    minHeight: 500,
  });

  // Initialize chessboard
  const chessboard = createChessboard(boardContainer, {
    orientation: 'white',
    draggable: true,
    selectable: true,
    showCoordinates: true,
    showLegalMoves: true,
    highlightLastMove: true,
    onMove: (move: Move) => {
      console.log('Move made:', move);

      // Update info bar
      const position = chessboard.getPosition();
      turnIndicator.textContent = `${position.turn === 'white' ? 'White' : 'Black'}'s turn`;
      moveCounter.textContent = `Move: ${position.fullmoveNumber}`;

      // Add to move log
      const moveEntry = document.createElement('div');
      moveEntry.style.padding = '2px 0';
      moveEntry.textContent = `${position.fullmoveNumber}. ${formatMove(move)}`;
      moveList.appendChild(moveEntry);

      // Auto-scroll to bottom
      moveLog.scrollTop = moveLog.scrollHeight;
    },
    onSquareClick: (square) => {
      console.log('Square clicked:', square);
    },
  });

  // Setup button handlers
  flipBtn.addEventListener('click', () => {
    chessboard.flip();
  });

  resetBtn.addEventListener('click', () => {
    chessboard.reset();
    moveList.innerHTML = '';
    turnIndicator.textContent = "White's turn";
    moveCounter.textContent = 'Move: 1';
  });

  maxBtn.addEventListener('click', () => {
    panel.toggleMaximize();
  });

  closeBtn.addEventListener('click', () => {
    panel.destroy();
    chessboard.destroy();
    panelElement.remove();
  });

  // Focus panel
  panel.focus();
}

/**
 * Format move for display
 */
function formatMove(move: Move): string {
  const from = String.fromCharCode(97 + move.from.file) + (move.from.rank + 1);
  const to = String.fromCharCode(97 + move.to.file) + (move.to.rank + 1);
  return `${from}-${to}${move.promotion ? `=${move.promotion.charAt(0).toUpperCase()}` : ''}`;
}

/**
 * Create multiple chess panels to demonstrate window management
 */
export function createMultipleChessPanels(): void {
  // Create first panel at default position
  createChessPanel();

  // Create second panel offset
  setTimeout(() => {
    const panelElement = document.querySelector('.chess-panel') as HTMLElement;
    if (panelElement) {
      panelElement.style.left = '100px';
      panelElement.style.top = '100px';
    }
    createChessPanel();
  }, 100);
}

// Auto-initialize on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    // Uncomment to auto-create panel
    // createChessPanel();
  });
} else {
  // Uncomment to auto-create panel
  // createChessPanel();
}

// Export for manual initialization
(window as any).createChessPanel = createChessPanel;
(window as any).createMultipleChessPanels = createMultipleChessPanels;
