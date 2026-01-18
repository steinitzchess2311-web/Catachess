/**
 * Chessboard Component
 *
 * Main chessboard UI component with advanced piece dragging using core system,
 * move validation via backend, and visual feedback.
 *
 * IMPORTANT: All chess rules and move validation are handled by the backend.
 * This component only handles UI interactions and rendering.
 */

import type {
  ChessboardOptions,
  ChessboardState,
  Square,
  Piece,
  Move,
  BoardPosition,
} from '../types';
import {
  createInitialPosition,
  squareToAlgebraic,
  squaresEqual,
} from '../types';
import {
  getPieceImageUrl,
  nextPieceSet,
  getCurrentPieceSet,
} from '../../chess_pieces';
import { chessAPI } from '../utils/api';
import { PieceDragger } from './PieceDragger';
import { GameStorage, GameStorageOptions } from '../storage';

/**
 * Chessboard class
 */
export class Chessboard {
  private container: HTMLElement;
  private boardElement: HTMLElement;
  private options: Required<ChessboardOptions>;
  private state: ChessboardState;
  private pieceDragger: PieceDragger | null = null;
  private storage: GameStorage | null = null;
  private unsubscribers: (() => void)[] = [];

  constructor(container: HTMLElement, options: ChessboardOptions = {}) {
    this.container = container;

    // Set default options
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
      validateMove: options.validateMove || this.defaultValidateMove.bind(this),
      onSaved: options.onSaved || (() => {}),
      onStorageError: options.onStorageError || ((error) => console.error('Storage error:', error)),
    };

    // Initialize state
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

    // Initialize storage if enabled
    if (this.options.enableStorage) {
      this.setupStorage();
    }

    this.render();
    this.setupEventListeners();
    this.setupPieceDragger();
  }

  /**
   * Setup game storage (auto-save)
   */
  private setupStorage(): void {
    this.storage = new GameStorage({
      autoSave: true,
      gameInfo: {
        gameId: this.options.gameId || `game_${Date.now()}`,
      },
      onSaved: (gameId) => {
        this.options.onSaved(gameId);
      },
      onError: (error) => {
        this.options.onStorageError(error);
      },
    });
  }

  /**
   * Setup piece dragging using core drag system
   */
  private setupPieceDragger(): void {
    if (!this.options.draggable) return;

    this.pieceDragger = new PieceDragger(this.boardElement, {
      onDragStart: (square, piece) => {
        // Only allow dragging pieces of the current player
        if (piece.color !== this.state.position.turn) {
          return false; // Cancel drag
        }

        this.state.isDragging = true;
        this.state.draggedPiece = { piece, from: square };
        return true;
      },

      onDrag: (fromSquare, toSquare, piece) => {
        // Visual feedback during drag (handled by PieceDragger)
      },

      onDrop: async (fromSquare, toSquare, piece) => {
        // Attempt to make the move
        const move: Move = {
          from: fromSquare,
          to: toSquare,
          piece,
        };

        const success = await this.makeMove(move);

        this.state.isDragging = false;
        this.state.draggedPiece = null;

        return success;
      },

      onDragCancel: () => {
        this.state.isDragging = false;
        this.state.draggedPiece = null;
      },

      getLegalMoves: async (square) => {
        // Get legal moves from backend for visual feedback
        if (this.options.showLegalMoves) {
          return await chessAPI.getLegalMoves(this.state.position, square);
        }
        return [];
      },

      validateDrop: (fromSquare, toSquare) => {
        // Basic client-side validation
        // Real validation happens on backend
        return true;
      },
    });
  }

  /**
   * Render the chessboard
   */
  private render(): void {
    // Main container setup
    this.container.innerHTML = '';
    this.container.style.position = 'relative';
    this.container.style.width = '100%';
    this.container.style.height = '100%';

    // Create and style the "Change Pieces" button
    const changePiecesButton = document.createElement('button');
    changePiecesButton.textContent = `Pieces: ${getCurrentPieceSet().name}`;
    changePiecesButton.className = 'change-pieces-btn';
    
    changePiecesButton.addEventListener('click', () => {
      nextPieceSet();
      this.render(); // Re-render to update piece set
    });

    this.container.appendChild(changePiecesButton);
    
    // Create and add the board element
    this.boardElement.className = 'chessboard';
    this.boardElement.innerHTML = '';

    for (let rank = 7; rank >= 0; rank--) {
      for (let file = 0; file < 8; file++) {
        const displayRank = this.state.isFlipped ? 7 - rank : rank;
        const displayFile = this.state.isFlipped ? 7 - file : file;

        const square = this.createSquareElement({ file: displayFile, rank: displayRank });
        this.boardElement.appendChild(square);
      }
    }

    this.container.appendChild(this.boardElement);
    this.applyStyles();
  }

  /**
   * Create a square element
   */
  private createSquareElement(square: Square): HTMLElement {
    const squareElement = document.createElement('div');
    squareElement.className = 'square';
    squareElement.dataset.file = String(square.file);
    squareElement.dataset.rank = String(square.rank);

    // Add light/dark class
    const isLight = (square.file + square.rank) % 2 === 0;
    squareElement.classList.add(isLight ? 'light' : 'dark');

    // Add coordinates
    if (this.options.showCoordinates) {
      if (square.file === 0) {
        const rankLabel = document.createElement('div');
        rankLabel.className = 'rank-label';
        rankLabel.textContent = String(square.rank + 1);
        squareElement.appendChild(rankLabel);
      }

      if (square.rank === 0) {
        const fileLabel = document.createElement('div');
        fileLabel.className = 'file-label';
        fileLabel.textContent = String.fromCharCode(97 + square.file);
        squareElement.appendChild(fileLabel);
      }
    }

    // Add piece if present
    const piece = this.state.position.squares[square.rank][square.file];
    if (piece) {
      const pieceElement = this.createPieceElement(piece, square);
      squareElement.appendChild(pieceElement);
    }

    // Highlight if needed
    if (this.shouldHighlightSquare(square)) {
      squareElement.classList.add('highlighted');
    }

    if (this.state.selectedSquare && squaresEqual(this.state.selectedSquare, square)) {
      squareElement.classList.add('selected');
    }

    return squareElement;
  }

  /**
   * Create a piece element
   */
  private createPieceElement(piece: Piece, square: Square): HTMLElement {
    const pieceElement = document.createElement('img');
    pieceElement.className = `piece ${piece.color} ${piece.type}`;
    pieceElement.src = getPieceImageUrl(piece);
    
    // Accessibility
    pieceElement.alt = `${piece.color} ${piece.type}`;
    
    // Set data attributes
    pieceElement.dataset.color = piece.color;
    pieceElement.dataset.type = piece.type;
    pieceElement.dataset.square = squareToAlgebraic(square);

    // Add cursor style for draggable pieces
    if (this.options.draggable && piece.color === this.state.position.turn) {
      pieceElement.style.cursor = 'grab';
    } else {
      pieceElement.style.cursor = 'default';
    }

    return pieceElement;
  }

  /**
   * Check if square should be highlighted
   */
  private shouldHighlightSquare(square: Square): boolean {
    // Highlight legal move destinations
    if (this.options.showLegalMoves && this.state.selectedSquare) {
      return this.state.legalMoves.some((move) => squaresEqual(move.to, square));
    }

    // Highlight last move
    if (this.options.highlightLastMove && this.state.lastMove) {
      return (
        squaresEqual(this.state.lastMove.from, square) ||
        squaresEqual(this.state.lastMove.to, square)
      );
    }

    return false;
  }

  /**
   * Setup event listeners (for click-to-move)
   */
  private setupEventListeners(): void {
    if (!this.options.selectable) return;

    // Square click handler for click-to-move
    this.boardElement.addEventListener('click', this.handleSquareClick.bind(this));
  }

  /**
   * Handle square click (for click-to-move)
   */
  private handleSquareClick(event: MouseEvent): void {
    const target = event.target as HTMLElement;
    const squareElement = target.closest('.square') as HTMLElement;

    if (!squareElement) return;

    const file = parseInt(squareElement.dataset.file || '0');
    const rank = parseInt(squareElement.dataset.rank || '0');
    const square: Square = { file, rank };

    // Call callback
    this.options.onSquareClick(square);

    // Handle piece selection
    this.handlePieceSelection(square);
  }

  private getSquareElement(square: Square): HTMLElement | null {
    return this.boardElement.querySelector(
      `.square[data-file='${square.file}'][data-rank='${square.rank}']`
    );
  }

  /**
   * Update the board UI after a move
   */
  private updateBoardUI(move: Move): void {
    const fromSquareEl = this.getSquareElement(move.from);
    const toSquareEl = this.getSquareElement(move.to);

    if (!fromSquareEl || !toSquareEl) return;

    // Move the piece
    const pieceEl = fromSquareEl.querySelector('.piece');
    if (pieceEl) {
      // Check for capture
      const capturedPieceEl = toSquareEl.querySelector('.piece');
      if (capturedPieceEl) {
        capturedPieceEl.remove();
      }

      toSquareEl.appendChild(pieceEl);

      // Update piece element's data attributes
      pieceEl.setAttribute('data-square', squareToAlgebraic(move.to));
    }

    // Update highlights
    this.updateSelectionUI();
  }

  /**
   * Update UI for selection changes
   */
  private updateSelectionUI(): void {
    // Clear all previous highlights
    this.boardElement
      .querySelectorAll('.selected, .highlighted')
      .forEach((el) => {
        el.classList.remove('selected', 'highlighted');
      });

    // Highlight selected square
    if (this.state.selectedSquare) {
      const selectedSquareEl = this.getSquareElement(this.state.selectedSquare);
      if (selectedSquareEl) {
        selectedSquareEl.classList.add('selected');
      }
    }

    // Highlight legal moves
    if (this.options.showLegalMoves && this.state.legalMoves.length > 0) {
      this.state.legalMoves.forEach((move) => {
        const toSquareEl = this.getSquareElement(move.to);
        if (toSquareEl) {
          toSquareEl.classList.add('highlighted');
        }
      });
    }

    // Highlight last move
    if (this.options.highlightLastMove && this.state.lastMove) {
      const fromEl = this.getSquareElement(this.state.lastMove.from);
      const toEl = this.getSquareElement(this.state.lastMove.to);
      if (fromEl) fromEl.classList.add('highlighted');
      if (toEl) toEl.classList.add('highlighted');
    }
  }

  /**
   * Handle piece selection (click-to-move mode)
   */
  private async handlePieceSelection(square: Square): Promise<void> {
    const piece = this.state.position.squares[square.rank][square.file];

    // If clicking on own piece, select it
    if (piece && piece.color === this.state.position.turn) {
      this.state.selectedSquare = square;

      // Get legal moves for this piece from backend
      this.state.legalMoves = await chessAPI.getLegalMoves(this.state.position, square);

      this.options.onPieceSelect(square, piece);
      this.updateSelectionUI(); // <-- Replaced render()
      return;
    }

    // If a piece is selected, try to move to clicked square
    if (this.state.selectedSquare) {
      const move: Move = {
        from: this.state.selectedSquare,
        to: square,
      };

      const success = await this.makeMove(move);

      // Clear selection
      this.state.selectedSquare = null;
      this.state.legalMoves = [];
      
      if(success) {
        this.updateSelectionUI();
      }
    }
  }

  /**
   * Make a move (validates via backend)
   */
  private async makeMove(move: Move): Promise<boolean> {
    // Validate move via backend
    const isValid = await this.options.validateMove(move);

    if (!isValid) {
      console.warn('Invalid move:', move);
      return false;
    }

    try {
      // Apply move via backend and get new position
      const newPosition = await chessAPI.applyMove(this.state.position, move);

      // Update state
      this.state.position = newPosition;
      this.state.lastMove = move;

      // Auto-save to backend if storage is enabled
      if (this.storage && this.storage.isAutoSaveEnabled()) {
        await this.storage.saveMove({
          gameId: this.storage.getGameId()!,
          move: move,
          position: newPosition,
        });
      }

      // Call callback
      this.options.onMove(move);

      // Update UI
      this.updateBoardUI(move);

      return true;
    } catch (error) {
      console.error('Failed to make move:', error);
      return false;
    }
  }

  /**
   * Default move validation (calls backend)
   */
  private async defaultValidateMove(move: Move): Promise<boolean> {
    return await chessAPI.validateMove(this.state.position, move);
  }

  /**
   * Apply CSS styles
   */
  private applyStyles(): void {
    const styleId = 'chessboard-styles';
    if (document.getElementById(styleId)) {
      // Remove old styles to apply new ones
      document.getElementById(styleId)!.remove();
    }

    const style = document.createElement('style');
    style.id = styleId;
    style.textContent = `
      .change-pieces-btn {
        position: absolute;
        top: -30px;
        right: 0;
        padding: 4px 8px;
        background: #4a4a4a;
        color: white;
        border: 1px solid #6a6a6a;
        border-radius: 4px;
        cursor: pointer;
        font-size: 0.9em;
        z-index: 10;
      }

      .change-pieces-btn:hover {
        background: #6a6a6a;
      }
      
      .chessboard {
        display: grid;
        grid-template-columns: repeat(8, 1fr);
        grid-template-rows: repeat(8, 1fr);
        width: 100%;
        height: 100%;
        aspect-ratio: 1;
        border: 2px solid #333;
        user-select: none;
      }

      .square {
        position: relative;
        display: flex;
        align-items: center;
        justify-content: center;
        aspect-ratio: 1;
      }

      .square.light {
        background: #f0d9b5;
      }

      .square.dark {
        background: #b58863;
      }

      .square.selected {
        background: #9bc700 !important;
      }

      .square.highlighted::after {
        content: '';
        position: absolute;
        width: 30%;
        height: 30%;
        background: rgba(0, 0, 0, 0.2);
        border-radius: 50%;
      }

      .square.legal-move::after {
        content: '';
        position: absolute;
        width: 25%;
        height: 25%;
        background: rgba(20, 85, 30, 0.5);
        border-radius: 50%;
        pointer-events: none;
      }

      .square.hover {
        background: rgba(255, 255, 0, 0.3) !important;
      }

      .piece {
        width: 90%;
        height: 90%;
        object-fit: contain;
        user-select: none;
        pointer-events: auto;
        transition: opacity 0.1s;
      }

      .piece:active {
        cursor: grabbing !important;
      }

      .chessboard.piece-dragging .piece {
        pointer-events: none;
      }

      .rank-label, .file-label {
        position: absolute;
        font-size: 0.7em;
        font-weight: bold;
        color: rgba(0, 0, 0, 0.5);
        pointer-events: none;
        user-select: none;
      }

      .rank-label {
        top: 2px;
        left: 2px;
      }

      .file-label {
        bottom: 2px;
        right: 2px;
      }

      .piece-drag-ghost {
        position: fixed;
        pointer-events: none;
        z-index: 10000;
        font-size: 3em;
        opacity: 0.8;
        transform: translate(-50%, -50%);
        user-select: none;
      }
    `;
    
    document.head.appendChild(style);
  }

  /**
   * Flip board orientation
   */
  public flip(): void {
    this.state.isFlipped = !this.state.isFlipped;
    this.render();

    // Re-setup dragger with new DOM
    if (this.pieceDragger) {
      this.pieceDragger.destroy();
      this.setupPieceDragger();
    }
  }

  /**
   * Set position
   */
  public setPosition(position: BoardPosition): void {
    this.state.position = position;
    this.render();

    // Re-setup dragger
    if (this.pieceDragger) {
      this.pieceDragger.destroy();
      this.setupPieceDragger();
    }
  }

  /**
   * Get current position
   */
  public getPosition(): BoardPosition {
    return this.state.position;
  }

  /**
   * Reset to initial position
   */
  public reset(): void {
    this.state.position = createInitialPosition();
    this.state.selectedSquare = null;
    this.state.legalMoves = [];
    this.state.lastMove = null;
    this.render();

    // Re-setup dragger
    if (this.pieceDragger) {
      this.pieceDragger.destroy();
      this.setupPieceDragger();
    }
  }

  /**
   * Get storage instance
   */
  public getStorage(): GameStorage | null {
    return this.storage;
  }

  /**
   * Enable/disable auto-save
   */
  public setAutoSave(enabled: boolean): void {
    if (this.storage) {
      this.storage.setAutoSave(enabled);
    }
  }

  /**
   * Get game PGN from backend
   */
  public async getPGN(): Promise<string> {
    if (this.storage) {
      return await this.storage.getPGN();
    }
    return '';
  }

  /**
   * Add comment to last move
   */
  public async addComment(comment: string): Promise<boolean> {
    if (this.storage) {
      return await this.storage.addComment(comment);
    }
    return false;
  }

  /**
   * Add NAG (!, ?, !!, ??, etc.) to last move
   */
  public async addNAG(nag: number): Promise<boolean> {
    if (this.storage) {
      return await this.storage.addNAG(nag);
    }
    return false;
  }

  /**
   * Destroy and cleanup
   */
  public destroy(): void {
    if (this.pieceDragger) {
      this.pieceDragger.destroy();
    }
    this.unsubscribers.forEach((unsub) => unsub());
    this.container.innerHTML = '';
  }
}

/**
 * Create a chessboard instance
 */
export function createChessboard(
  container: HTMLElement,
  options?: ChessboardOptions
): Chessboard {
  return new Chessboard(container, options);
}
