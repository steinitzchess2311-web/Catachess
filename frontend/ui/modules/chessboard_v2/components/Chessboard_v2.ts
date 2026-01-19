/**
 * Chessboard V2 Component
 *
 * A new implementation of the chessboard with a focus on simplicity and modern APIs.
 */

import type {
  ChessboardOptions,
  ChessboardState,
  Square,
  Piece,
  Move,
  BoardPosition,
} from '../../chessboard/types';
import {
  createInitialPosition,
  squareToAlgebraic,
  squaresEqual,
} from '../../chessboard/types';
import {
  getPieceImageUrl,
  nextPieceSet,
  getCurrentPieceSet,
} from '../../chess_pieces';
import { chessAPI } from '../../chessboard/utils/api';

export class ChessboardV2 {
  private container: HTMLElement;
  private boardElement: HTMLElement;
  private options: Required<ChessboardOptions>;
  private state: ChessboardState;
  private handleClickBound: ((event: MouseEvent) => void) | null = null;
  private resizeObserver: ResizeObserver | null = null;
  private resizeHandler: (() => void) | null = null;

  constructor(container: HTMLElement, options: ChessboardOptions = {}) {
    this.container = container;

    this.options = {
      initialPosition: options.initialPosition || createInitialPosition(),
      orientation: options.orientation || 'white',
      draggable: options.draggable !== false,
      selectable: options.selectable !== false,
      showCoordinates: options.showCoordinates !== false,
      showLegalMoves: options.showLegalMoves !== false,
      highlightLastMove: options.highlightLastMove !== false,
      enableStorage: options.enableStorage || false,
      gameId: options.gameId,
      onMove: options.onMove || (() => {}),
      onPieceSelect: options.onPieceSelect || (() => {}),
      onSquareClick: options.onSquareClick || (() => {}),
      validateMove: options.validateMove || (async () => true),
      onSaved: options.onSaved || (() => {}),
      onStorageError: options.onStorageError || ((error) => console.error('Storage error:', error)),
    };

    this.state = {
      position: this.options.initialPosition,
      selectedSquare: null,
      legalMoves: [],
      highlightedSquares: [],
      lastMove: null,
      isFlipped: this.options.orientation === 'black',
      isDragging: false,
      draggedPiece: null,
    };

    this.boardElement = document.createElement('div');

    this.render();
    this.applyStyles();
    this.setupEventListeners();
    this.setupResizeHandling();
  }

  private render(): void {
    this.container.innerHTML = '';
    this.container.style.position = 'relative';
    this.container.style.width = '100%';
    this.container.style.height = '100%';
    this.container.style.display = 'flex';
    this.container.style.flexDirection = 'column';
    this.container.style.alignItems = 'center';

    const toolbar = document.createElement('div');
    toolbar.className = 'pieces-toolbar';

    const changePiecesButton = document.createElement('button');
    changePiecesButton.textContent = `Pieces: ${getCurrentPieceSet().name}`;
    changePiecesButton.className = 'change-pieces-btn';
    changePiecesButton.addEventListener('click', () => {
      nextPieceSet();
      changePiecesButton.textContent = `Pieces: ${getCurrentPieceSet().name}`;
      this.updateAllPieces();
    });
    toolbar.appendChild(changePiecesButton);
    this.container.appendChild(toolbar);

    this.boardElement.className = 'chessboard-v2';
    this.container.appendChild(this.boardElement);
    this.createInitialBoard();
  }

  private createInitialBoard(): void {
    this.boardElement.innerHTML = '';
    for (let rank = 7; rank >= 0; rank--) {
      for (let file = 0; file < 8; file++) {
        const squareData = { file, rank };
        const squareElement = this.createSquareElement(squareData);
        this.boardElement.appendChild(squareElement);
      }
    }
    this.updateAllPieces();
  }

  private createSquareElement(square: Square): HTMLElement {
    const squareElement = document.createElement('div');
    squareElement.className = 'square';
    squareElement.dataset.file = String(square.file);
    squareElement.dataset.rank = String(square.rank);

    const isLight = (square.file + square.rank) % 2 !== 0;
    squareElement.classList.add(isLight ? 'light' : 'dark');

    return squareElement;
  }

  private createPieceElement(piece: Piece, square: Square): HTMLElement {
    const pieceElement = document.createElement('img');
    pieceElement.className = `piece ${piece.color} ${piece.type}`;
    pieceElement.src = getPieceImageUrl(piece);
    pieceElement.draggable = false;
    pieceElement.alt = '';
    pieceElement.setAttribute('aria-label', `${piece.color} ${piece.type}`);
    pieceElement.addEventListener('error', () => {
      pieceElement.removeAttribute('src');
      pieceElement.style.visibility = 'hidden';
    });
    pieceElement.dataset.color = piece.color;
    pieceElement.dataset.type = piece.type;
    pieceElement.dataset.square = squareToAlgebraic(square);
    if (this.options.selectable && piece.color === this.state.position.turn) {
      pieceElement.style.cursor = 'pointer';
    }
    return pieceElement;
  }

  private getSquareElement(square: Square): HTMLElement | null {
    const { file, rank } = this.state.isFlipped
      ? { file: 7 - square.file, rank: 7 - square.rank }
      : square;
    return this.boardElement.querySelector(
      `.square[data-file='${file}'][data-rank='${rank}']`
    );
  }

  private updateAllPieces(): void {
    for (let rank = 0; rank < 8; rank++) {
      for (let file = 0; file < 8; file++) {
        const square = { rank, file };
        const squareEl = this.getSquareElement(square);
        if (!squareEl) continue;

        const piece = this.state.position.squares[rank][file];
        const pieceEl = squareEl.querySelector('.piece');

        if (piece && !pieceEl) {
          const newPieceEl = this.createPieceElement(piece, square);
          squareEl.appendChild(newPieceEl);
        } else if (!piece && pieceEl) {
          pieceEl.remove();
        } else if (piece && pieceEl) {
          const newSrc = getPieceImageUrl(piece);
          if (pieceEl.getAttribute('src') !== newSrc) {
            (pieceEl as HTMLImageElement).src = newSrc;
          }
          if (pieceEl.getAttribute('data-color') !== piece.color || pieceEl.getAttribute('data-type') !== piece.type) {
            pieceEl.className = `piece ${piece.color} ${piece.type}`;
            pieceEl.setAttribute('data-color', piece.color);
            pieceEl.setAttribute('data-type', piece.type);
          }
        }
      }
    }
    this.updateSelectionUI();
  }

  private updateBoardUI(move: Move): void {
    const fromSquareEl = this.getSquareElement(move.from);
    const toSquareEl = this.getSquareElement(move.to);

    if (!fromSquareEl || !toSquareEl) return;

    const pieceEl = fromSquareEl.querySelector('.piece');
    if (pieceEl) {
      const capturedPieceEl = toSquareEl.querySelector('.piece');
      if (capturedPieceEl) {
        capturedPieceEl.remove();
      }
      toSquareEl.appendChild(pieceEl);
      pieceEl.setAttribute('data-square', squareToAlgebraic(move.to));
    }
    this.updateSelectionUI();
  }

  private updateSelectionUI(): void {
    this.boardElement.querySelectorAll('.selected, .legal-move, .last-move').forEach((el) => {
      el.classList.remove('selected', 'legal-move', 'last-move');
    });

    if (this.state.selectedSquare) {
      const selectedSquareEl = this.getSquareElement(this.state.selectedSquare);
      selectedSquareEl?.classList.add('selected');
    }

    if (this.options.showLegalMoves) {
      this.state.legalMoves.forEach((move) => {
        const toSquareEl = this.getSquareElement(move.to);
        toSquareEl?.classList.add('legal-move');
      });
    }

    if (this.options.highlightLastMove && this.state.lastMove) {
      const fromEl = this.getSquareElement(this.state.lastMove.from);
      fromEl?.classList.add('last-move');
      const toEl = this.getSquareElement(this.state.lastMove.to);
      toEl?.classList.add('last-move');
    }
  }


  private setupEventListeners(): void {
    this.handleClickBound = this.handleSquareClick.bind(this);
    this.boardElement.addEventListener('click', this.handleClickBound);
    this.boardElement.addEventListener('dragstart', (event) => {
      event.preventDefault();
    });
    this.boardElement.addEventListener('pointerdown', (event) => {
      const target = event.target as HTMLElement | null;
      if (target?.closest('.piece')) {
        event.preventDefault();
      }
    });
  }

  private async handleSquareClick(event: MouseEvent): Promise<void> {
    const target = event.target as HTMLElement;
    const squareElement = target.closest('.square') as HTMLElement;
    if (!squareElement) return;

    const file = parseInt(squareElement.dataset.file || '0', 10);
    const rank = parseInt(squareElement.dataset.rank || '0', 10);
    const square = this.state.isFlipped ? { file: 7 - file, rank: 7 - rank } : { file, rank };

    this.options.onSquareClick(square);
    const piece = this.state.position.squares[square.rank][square.file];

    // Case 1: Select a piece (or re-select/change selection)
    if (piece && piece.color === this.state.position.turn) {
      this.state.selectedSquare = square;
      this.state.legalMoves = [];
      this.updateSelectionUI(); // Immediate feedback for selection
      this.options.onPieceSelect(square, piece);

      // Fetch legal moves async for highlighting, but don't block the UI
      chessAPI.getLegalMoves(this.state.position, square).then(moves => {
        // Only update highlights if the selection hasn't changed
        if (this.state.selectedSquare && squaresEqual(this.state.selectedSquare, square)) {
          this.state.legalMoves = moves;
          this.updateSelectionUI();
        }
      });
      return;
    }

    // Case 2: Make a move
    if (this.state.selectedSquare) {
      const fromSquare = this.state.selectedSquare;
      const move: Move = { from: fromSquare, to: square };
      
      this.state.selectedSquare = null;
      this.state.legalMoves = [];
      
      const success = await this.makeMove(move);
      if (success) {
          this.options.onMove(move);
      } else {
        // If makeMove fails, the UI is reverted within it.
        // We just call updateSelectionUI to clear any lingering highlights.
        this.updateSelectionUI();
      }
    }
  }

  private async makeMove(move: Move): Promise<boolean> {
    const originalPosition = JSON.parse(JSON.stringify(this.state.position));
    const piece = this.state.position.squares[move.from.rank][move.from.file];
    if (!piece) return false;

    // Optimistic UI update
    this.state.position.squares[move.to.rank][move.to.file] = piece;
    this.state.position.squares[move.from.rank][move.from.file] = null;
    this.state.position.turn = this.state.position.turn === 'white' ? 'black' : 'white';
    this.state.lastMove = move;
    this.updateBoardUI(move);

    try {
      const isValid = await this.options.validateMove(move);
      if (!isValid) throw new Error("Move validation failed");

      const result = await chessAPI.applyMove(originalPosition, move);
      // The backend is the source of truth, so we sync our state with it.
      this.state.position = result.position; 
      this.state.lastMove = move; // Keep our last move for highlighting
      this.updateAllPieces(); // Sync entire board with backend state
      return true;
    } catch (error) {
      console.error("Failed to apply move, reverting:", error);
      // Revert state and UI
      this.state.position = originalPosition;
      this.state.lastMove = null;
      this.updateAllPieces();
      return false;
    }
  }

  private applyStyles(): void {
    const styleId = 'chessboard-v2-styles';
    if (document.getElementById(styleId)) return;

    const style = document.createElement('style');
    style.id = styleId;
    style.textContent = `
      .chessboard-v2 {
        display: grid;
        grid-template-columns: repeat(8, 1fr);
        grid-template-rows: repeat(8, 1fr);
        width: 100%;
        height: auto;
        aspect-ratio: 1 / 1;
        box-sizing: border-box;
        background-color: #b58863;
        line-height: 0;
        font-size: 0;
      }
      .chessboard-v2 .square {
        position: relative;
        box-sizing: border-box;
        aspect-ratio: 1 / 1;
        overflow: hidden;
      }
      .chessboard-v2 .square.selected {
        box-shadow: inset 0 0 0 3px #173a7a;
      }
      .chessboard-v2 .square.light { background-color: #f0d9b5; }
      .chessboard-v2 .square.dark { background-color: #b58863; }

      .chessboard-v2 .square.last-move {
        background-color: #cdd26a !important;
      }

      .chessboard-v2 .square.legal-move::after {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 35%;
        height: 35%;
        background-color: rgba(23, 58, 122, 0.4);
        border-radius: 50%;
        pointer-events: none;
      }

      .chessboard-v2 .piece {
        display: block;
        width: 100%;
        height: 100%;
        object-fit: contain;
        cursor: default;
        -webkit-user-drag: none;
        -webkit-user-select: none;
        pointer-events: none;
        touch-action: none;
      }
      .chessboard-v2 .piece.white.pawn {
        transform: scale(0.95);
        transform-origin: center;
      }
      .pieces-toolbar {
        width: 100%;
        max-width: 480px;
        display: flex;
        justify-content: flex-end;
        margin-bottom: 12px;
      }
      .change-pieces-btn {
        padding: 6px 12px;
        border-radius: 8px;
        border: 1px solid rgba(0, 0, 0, 0.15);
        background: #f8f6f2;
        color: #3a2f26;
        font-weight: 600;
        cursor: pointer;
      }
      .change-pieces-btn:hover {
        background: #efeae1;
      }
    `;
    document.head.appendChild(style);
  }

  private setupResizeHandling(): void {
    this.resizeObserver = new ResizeObserver(() => {
      this.syncSquareSize();
    });
    this.resizeObserver.observe(this.container);
  }

  private syncSquareSize(): void {
    // No longer needed to manually set grid sizes due to aspect-ratio and fr units
    // We keep this function in case we need more complex resize logic later.
    // For example, adjusting font sizes or other elements based on board size.
  }

  public flip(): void {
    this.state.isFlipped = !this.state.isFlipped;
    this.createInitialBoard();
  }

  public setPosition(position: BoardPosition): void {
    this.state.position = position;
    this.updateAllPieces();
  }

  public getPosition(): BoardPosition {
    return this.state.position;
  }

  public reset(): void {
    this.state.position = createInitialPosition();
    this.state.selectedSquare = null;
    this.state.legalMoves = [];
    this.state.lastMove = null;
    this.updateAllPieces();
  }

  public destroy(): void {
    if (this.handleClickBound) {
      this.boardElement.removeEventListener('click', this.handleClickBound);
    }
    if (this.resizeObserver) {
      this.resizeObserver.disconnect();
      this.resizeObserver = null;
    }
    if (this.resizeHandler) {
      window.removeEventListener('resize', this.resizeHandler);
      this.resizeHandler = null;
    }
    this.container.innerHTML = '';
  }
}
