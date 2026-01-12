/**
 * Chessboard with Engine Analysis Example
 *
 * This example demonstrates:
 * 1. Creating a chessboard with drag-and-drop
 * 2. Integrating Stockfish engine analysis
 * 3. Displaying engine spot metrics
 * 4. Auto-updating analysis after moves
 */

import { createChessboard, createEngineAnalysis, type Move } from '../modules/chessboard';

/**
 * Initialize the chessboard with analysis
 */
export function initChessboardWithAnalysis() {
  // Get containers
  const boardContainer = document.getElementById('chessboard-container');
  const analysisContainer = document.getElementById('analysis-container');

  if (!boardContainer || !analysisContainer) {
    console.error('Required containers not found');
    return;
  }

  // Create engine analysis component
  const engineAnalysis = createEngineAnalysis(analysisContainer as HTMLElement, {
    onLineClick: (line) => {
      console.log('Line clicked:', line);
      // TODO: Show variation on board
    },
    autoRefreshMetrics: true,
    metricsRefreshInterval: 5000, // Refresh metrics every 5 seconds
  });

  // Create chessboard
  const chessboard = createChessboard(boardContainer as HTMLElement, {
    draggable: true,
    showLegalMoves: true,
    highlightLastMove: true,
    onMove: (move: Move) => {
      console.log('Move made:', move);

      // Update analysis component with new position
      const position = chessboard.getPosition();
      engineAnalysis.setPosition(position);

      // Optionally auto-analyze after each move
      // Uncomment to enable:
      // setTimeout(() => engineAnalysis.analyze(), 500);
    },
  });

  // Set initial position for analysis
  engineAnalysis.setPosition(chessboard.getPosition());

  // Add example controls
  addExampleControls(chessboard, engineAnalysis);
}

/**
 * Add example controls
 */
function addExampleControls(chessboard: any, engineAnalysis: any) {
  const controlsContainer = document.getElementById('controls-container');
  if (!controlsContainer) return;

  // Flip board button
  const flipBtn = document.createElement('button');
  flipBtn.textContent = 'Flip Board';
  flipBtn.onclick = () => chessboard.flip();
  controlsContainer.appendChild(flipBtn);

  // Reset button
  const resetBtn = document.createElement('button');
  resetBtn.textContent = 'Reset';
  resetBtn.onclick = () => {
    chessboard.reset();
    engineAnalysis.setPosition(chessboard.getPosition());
  };
  controlsContainer.appendChild(resetBtn);

  // Auto-analyze toggle
  let autoAnalyze = false;
  const autoAnalyzeBtn = document.createElement('button');
  autoAnalyzeBtn.textContent = 'Auto-Analyze: OFF';
  autoAnalyzeBtn.onclick = () => {
    autoAnalyze = !autoAnalyze;
    autoAnalyzeBtn.textContent = `Auto-Analyze: ${autoAnalyze ? 'ON' : 'OFF'}`;

    if (autoAnalyze) {
      engineAnalysis.analyze();
    }
  };
  controlsContainer.appendChild(autoAnalyzeBtn);
}

/**
 * HTML structure for the example:
 *
 * ```html
 * <!DOCTYPE html>
 * <html>
 * <head>
 *   <title>Chessboard with Engine Analysis</title>
 *   <style>
 *     body {
 *       margin: 0;
 *       padding: 20px;
 *       background: #2c2c2c;
 *       font-family: Arial, sans-serif;
 *     }
 *
 *     .container {
 *       display: grid;
 *       grid-template-columns: 600px 420px;
 *       gap: 20px;
 *       max-width: 1040px;
 *       margin: 0 auto;
 *     }
 *
 *     #chessboard-container {
 *       width: 600px;
 *       height: 600px;
 *     }
 *
 *     #analysis-container {
 *       width: 400px;
 *     }
 *
 *     #controls-container {
 *       grid-column: 1 / -1;
 *       display: flex;
 *       gap: 12px;
 *       justify-content: center;
 *     }
 *
 *     button {
 *       padding: 10px 20px;
 *       background: #4caf50;
 *       color: white;
 *       border: none;
 *       border-radius: 6px;
 *       font-size: 14px;
 *       cursor: pointer;
 *       transition: background 0.2s;
 *     }
 *
 *     button:hover {
 *       background: #45a049;
 *     }
 *   </style>
 * </head>
 * <body>
 *   <div class="container">
 *     <div id="chessboard-container"></div>
 *     <div id="analysis-container"></div>
 *     <div id="controls-container"></div>
 *   </div>
 *
 *   <script type="module">
 *     import { initChessboardWithAnalysis } from './chessboard-with-analysis-example.js';
 *     initChessboardWithAnalysis();
 *   </script>
 * </body>
 * </html>
 * ```
 */

/**
 * Advanced example with move history and annotations
 */
export function initAdvancedExample() {
  const boardContainer = document.getElementById('chessboard-container');
  const analysisContainer = document.getElementById('analysis-container');
  const historyContainer = document.getElementById('history-container');

  if (!boardContainer || !analysisContainer || !historyContainer) {
    console.error('Required containers not found');
    return;
  }

  // Move history
  const moveHistory: Move[] = [];

  // Create engine analysis
  const engineAnalysis = createEngineAnalysis(analysisContainer as HTMLElement, {
    onLineClick: (line) => {
      console.log('Suggested line:', line.pv);
      // Could implement "show variation" feature here
    },
  });

  // Create chessboard with storage
  const chessboard = createChessboard(boardContainer as HTMLElement, {
    draggable: true,
    showLegalMoves: true,
    highlightLastMove: true,
    enableStorage: true,
    gameId: `game_${Date.now()}`,
    onMove: (move: Move) => {
      // Add to history
      moveHistory.push(move);
      updateMoveHistory(historyContainer as HTMLElement, moveHistory);

      // Update analysis
      engineAnalysis.setPosition(chessboard.getPosition());
    },
    onSaved: (gameId) => {
      console.log('Game saved:', gameId);
    },
  });

  // Initialize
  engineAnalysis.setPosition(chessboard.getPosition());
}

/**
 * Update move history display
 */
function updateMoveHistory(container: HTMLElement, history: Move[]) {
  container.innerHTML = '<h3>Move History</h3>';

  const list = document.createElement('div');
  list.style.cssText = `
    max-height: 400px;
    overflow-y: auto;
    padding: 10px;
    background: #1e1e1e;
    border-radius: 6px;
  `;

  history.forEach((move, index) => {
    const moveNum = Math.floor(index / 2) + 1;
    const isWhite = index % 2 === 0;

    const moveEl = document.createElement('div');
    moveEl.textContent = `${isWhite ? moveNum + '.' : ''} ${move.from.file}${
      move.from.rank
    } → ${move.to.file}${move.to.rank}`;
    moveEl.style.cssText = `
      padding: 6px;
      color: #e0e0e0;
      font-family: monospace;
    `;

    list.appendChild(moveEl);
  });

  container.appendChild(list);
}

// Auto-initialize if running in browser
if (typeof window !== 'undefined') {
  window.addEventListener('DOMContentLoaded', () => {
    initChessboardWithAnalysis();
  });
}
