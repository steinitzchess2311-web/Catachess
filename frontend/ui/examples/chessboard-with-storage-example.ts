/**
 * Chessboard with Auto-Save Example
 *
 * Demonstrates chessboard with automatic PGN saving to backend.
 * Every move is automatically saved, including variations.
 *
 * IMPORTANT: Frontend only triggers save events.
 * Backend handles PGN generation, variations, and R2 storage.
 */

import { createPanel } from '../core';
import { createChessboard } from '../modules/chessboard';
import type { Move } from '../modules/chessboard';

/**
 * Create a chess panel with auto-save enabled
 */
export function createChessPanelWithStorage(): void {
  // Create panel container
  const panelElement = document.createElement('div');
  panelElement.className = 'chess-panel';
  panelElement.style.cssText = `
    position: absolute;
    left: 50px;
    top: 50px;
    width: 700px;
    height: 800px;
    background: white;
    border: 1px solid #ccc;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    overflow: hidden;
    display: flex;
    flex-direction: column;
  `;

  document.body.appendChild(panelElement);

  // Create header
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
  title.textContent = 'Chess Board (Auto-Save Enabled)';
  title.style.margin = '0';
  title.style.fontSize = '16px';

  const controls = document.createElement('div');
  controls.style.cssText = 'display: flex; gap: 8px;';

  // Save indicator
  const saveIndicator = document.createElement('span');
  saveIndicator.textContent = '💾 Saved';
  saveIndicator.style.cssText = `
    padding: 4px 12px;
    background: #27ae60;
    color: white;
    border-radius: 4px;
    font-size: 12px;
    opacity: 0;
    transition: opacity 0.3s;
  `;

  // Export PGN button
  const exportBtn = document.createElement('button');
  exportBtn.textContent = '📄 Export PGN';
  exportBtn.style.cssText = `
    padding: 4px 12px;
    background: #3498db;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  `;

  // Comment button
  const commentBtn = document.createElement('button');
  commentBtn.textContent = '💬 Add Comment';
  commentBtn.style.cssText = `
    padding: 4px 12px;
    background: #9b59b6;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  `;

  // Annotation buttons
  const goodMoveBtn = document.createElement('button');
  goodMoveBtn.textContent = '!';
  goodMoveBtn.title = 'Good move';
  goodMoveBtn.style.cssText = `
    padding: 4px 12px;
    background: #16a085;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-weight: bold;
  `;

  const mistakeBtn = document.createElement('button');
  mistakeBtn.textContent = '?';
  mistakeBtn.title = 'Mistake';
  mistakeBtn.style.cssText = `
    padding: 4px 12px;
    background: #e67e22;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-weight: bold;
  `;

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

  controls.appendChild(saveIndicator);
  controls.appendChild(exportBtn);
  controls.appendChild(commentBtn);
  controls.appendChild(goodMoveBtn);
  controls.appendChild(mistakeBtn);
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

  const gameId = `game_${Date.now()}`;
  const gameInfo = document.createElement('span');
  gameInfo.textContent = `Game ID: ${gameId.substring(5, 15)}...`;
  gameInfo.style.fontSize = '12px';
  gameInfo.style.color = '#7f8c8d';

  infoBar.appendChild(turnIndicator);
  infoBar.appendChild(gameInfo);
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
    height: 200px;
    padding: 12px;
    background: #f8f9fa;
    border-top: 1px solid #dee2e6;
    overflow-y: auto;
    font-family: monospace;
    font-size: 12px;
  `;

  const moveLogTitle = document.createElement('div');
  moveLogTitle.textContent = 'Move History (Auto-Saved)';
  moveLogTitle.style.cssText = 'font-weight: bold; margin-bottom: 8px;';
  moveLog.appendChild(moveLogTitle);

  const moveList = document.createElement('div');
  moveList.className = 'move-list';
  moveLog.appendChild(moveList);

  panelElement.appendChild(moveLog);

  // Initialize panel with window management
  const panel = createPanel({
    id: `chess-panel-${Date.now()}`,
    element: panelElement,
    draggable: true,
    resizable: true,
    focusable: true,
    snapEnabled: true,
    dragHandle: header,
    minWidth: 500,
    minHeight: 600,
  });

  // Initialize chessboard with storage enabled
  const chessboard = createChessboard(boardContainer, {
    orientation: 'white',
    draggable: true,
    selectable: true,
    showCoordinates: true,
    showLegalMoves: true,
    highlightLastMove: true,
    enableStorage: true, // Enable auto-save
    gameId: gameId,
    onMove: (move: Move) => {
      console.log('Move made:', move);

      // Update info bar
      const position = chessboard.getPosition();
      turnIndicator.textContent = `${position.turn === 'white' ? 'White' : 'Black'}'s turn`;

      // Add to move log
      const moveEntry = document.createElement('div');
      moveEntry.style.padding = '2px 0';
      moveEntry.textContent = `${position.fullmoveNumber}. ${formatMove(move)}`;
      moveList.appendChild(moveEntry);

      // Auto-scroll to bottom
      moveLog.scrollTop = moveLog.scrollHeight;
    },
    onSaved: (savedGameId) => {
      // Show save indicator
      saveIndicator.style.opacity = '1';
      setTimeout(() => {
        saveIndicator.style.opacity = '0';
      }, 2000);

      console.log('Game auto-saved:', savedGameId);
    },
    onStorageError: (error) => {
      console.error('Storage error:', error);
      alert(`Failed to save game: ${error.message}`);
    },
  });

  // Export PGN button
  exportBtn.addEventListener('click', async () => {
    const pgn = await chessboard.getPGN();

    if (pgn) {
      // Create download
      const blob = new Blob([pgn], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `game_${Date.now()}.pgn`;
      a.click();
      URL.revokeObjectURL(url);

      // Also show in console
      console.log('PGN:\n', pgn);
    } else {
      alert('No game data to export');
    }
  });

  // Add comment button
  commentBtn.addEventListener('click', async () => {
    const comment = prompt('Enter comment for last move:');
    if (comment) {
      const success = await chessboard.addComment(comment);
      if (success) {
        alert('Comment added!');
      }
    }
  });

  // Good move annotation
  goodMoveBtn.addEventListener('click', async () => {
    const success = await chessboard.addNAG(1); // NAG 1 = !
    if (success) {
      console.log('Added "!" annotation');
    }
  });

  // Mistake annotation
  mistakeBtn.addEventListener('click', async () => {
    const success = await chessboard.addNAG(2); // NAG 2 = ?
    if (success) {
      console.log('Added "?" annotation');
    }
  });

  // Close button
  closeBtn.addEventListener('click', () => {
    panel.destroy();
    chessboard.destroy();
    panelElement.remove();
  });

  // Focus panel
  panel.focus();

  // Log game info
  console.log('Chess panel created with auto-save');
  console.log('Game ID:', gameId);
  console.log('Every move will be automatically saved to backend');
}

/**
 * Format move for display
 */
function formatMove(move: Move): string {
  const from = String.fromCharCode(97 + move.from.file) + (move.from.rank + 1);
  const to = String.fromCharCode(97 + move.to.file) + (move.to.rank + 1);
  return `${from}-${to}${move.promotion ? `=${move.promotion.charAt(0).toUpperCase()}` : ''}`;
}

// Export for manual initialization
(window as any).createChessPanelWithStorage = createChessPanelWithStorage;

console.log('To create chess panel with auto-save: createChessPanelWithStorage()');
