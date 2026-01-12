/**
 * Piece Dragger - Advanced chess piece dragging
 *
 * Uses the core pointer system for smooth piece dragging with visual feedback.
 * All move validation is done by the backend.
 */

import { pointerManager, PointerEventData } from '../../../core/pointer';
import type { Square, Piece, Move } from '../types';
import { squaresEqual, squareToAlgebraic } from '../types';

export interface PieceDragOptions {
  onDragStart?: (square: Square, piece: Piece) => boolean | void;
  onDrag?: (fromSquare: Square, toSquare: Square | null, piece: Piece) => void;
  onDrop?: (fromSquare: Square, toSquare: Square, piece: Piece) => Promise<boolean>;
  onDragCancel?: () => void;
  getLegalMoves?: (square: Square) => Promise<Move[]>;
  validateDrop?: (fromSquare: Square, toSquare: Square) => boolean;
}

export interface DragState {
  active: boolean;
  piece: Piece | null;
  fromSquare: Square | null;
  currentSquare: Square | null;
  startX: number;
  startY: number;
  dragElement: HTMLElement | null;
  originalElement: HTMLElement | null;
  legalSquares: Square[];
}

/**
 * Chess piece dragger using core pointer system
 */
export class PieceDragger {
  private boardElement: HTMLElement;
  private options: PieceDragOptions;
  private state: DragState;
  private unsubscribers: (() => void)[] = [];
  private squareSize: number = 0;
  private boardRect: DOMRect | null = null;

  constructor(boardElement: HTMLElement, options: PieceDragOptions = {}) {
    this.boardElement = boardElement;
    this.options = options;

    this.state = {
      active: false,
      piece: null,
      fromSquare: null,
      currentSquare: null,
      startX: 0,
      startY: 0,
      dragElement: null,
      originalElement: null,
      legalSquares: [],
    };

    this.setupListeners();
  }

  /**
   * Setup event listeners
   */
  private setupListeners(): void {
    // Listen to pointer events from the board
    const handlePointerDown = (e: PointerEvent) => {
      const target = e.target as HTMLElement;
      const pieceElement = target.closest('.piece') as HTMLElement;

      if (!pieceElement) return;

      // Get square and piece info
      const squareElement = pieceElement.parentElement as HTMLElement;
      if (!squareElement || !squareElement.classList.contains('square')) return;

      const file = parseInt(squareElement.dataset.file || '0');
      const rank = parseInt(squareElement.dataset.rank || '0');
      const square: Square = { file, rank };

      const color = pieceElement.dataset.color as 'white' | 'black';
      const type = pieceElement.dataset.type as any;
      const piece: Piece = { color, type };

      this.startDrag(e, square, piece, pieceElement);
    };

    this.boardElement.addEventListener('pointerdown', handlePointerDown);
    this.unsubscribers.push(() => {
      this.boardElement.removeEventListener('pointerdown', handlePointerDown);
    });

    // Subscribe to pointer manager
    const unsubMove = pointerManager.on('move', this.handleDrag.bind(this));
    const unsubUp = pointerManager.on('up', this.handleDrop.bind(this));
    const unsubCancel = pointerManager.on('cancel', this.handleCancel.bind(this));

    this.unsubscribers.push(unsubMove, unsubUp, unsubCancel);
  }

  /**
   * Start dragging a piece
   */
  private async startDrag(
    e: PointerEvent,
    square: Square,
    piece: Piece,
    pieceElement: HTMLElement
  ): Promise<void> {
    e.preventDefault();
    e.stopPropagation();

    // Call onDragStart callback
    if (this.options.onDragStart) {
      const shouldContinue = this.options.onDragStart(square, piece);
      if (shouldContinue === false) return;
    }

    // Update board measurements
    this.boardRect = this.boardElement.getBoundingClientRect();
    this.squareSize = this.boardRect.width / 8;

    // Get legal moves for this piece
    if (this.options.getLegalMoves) {
      const legalMoves = await this.options.getLegalMoves(square);
      this.state.legalSquares = legalMoves.map((move) => move.to);
    }

    // Create drag element (ghost piece)
    const dragElement = this.createDragElement(piece);
    document.body.appendChild(dragElement);

    // Update state
    this.state.active = true;
    this.state.piece = piece;
    this.state.fromSquare = square;
    this.state.currentSquare = square;
    this.state.startX = e.clientX;
    this.state.startY = e.clientY;
    this.state.dragElement = dragElement;
    this.state.originalElement = pieceElement;

    // Position drag element at cursor
    this.updateDragElementPosition(e.clientX, e.clientY);

    // Hide original piece
    pieceElement.style.opacity = '0.3';

    // Add dragging class to board
    this.boardElement.classList.add('piece-dragging');

    // Highlight legal move squares
    this.highlightLegalSquares();
  }

  /**
   * Handle drag movement
   */
  private handleDrag(data: PointerEventData): void {
    if (!this.state.active || !this.state.dragElement) return;

    const { position } = data;

    // Update drag element position
    this.updateDragElementPosition(position.clientX, position.clientY);

    // Determine which square we're hovering over
    const hoverSquare = this.getSquareAtPosition(position.clientX, position.clientY);

    if (hoverSquare) {
      // Check if square changed
      if (!squaresEqual(this.state.currentSquare, hoverSquare)) {
        this.state.currentSquare = hoverSquare;

        // Call onDrag callback
        if (this.options.onDrag && this.state.piece && this.state.fromSquare) {
          this.options.onDrag(this.state.fromSquare, hoverSquare, this.state.piece);
        }

        // Update visual feedback
        this.updateSquareHighlight(hoverSquare);
      }
    } else {
      this.state.currentSquare = null;
      this.clearSquareHighlight();
    }
  }

  /**
   * Handle drop
   */
  private async handleDrop(data: PointerEventData): Promise<void> {
    if (!this.state.active) return;

    const { position } = data;

    // Get drop square
    const dropSquare = this.getSquareAtPosition(position.clientX, position.clientY);

    // Clean up drag element
    this.cleanupDragElement();

    if (
      dropSquare &&
      this.state.fromSquare &&
      this.state.piece &&
      !squaresEqual(dropSquare, this.state.fromSquare)
    ) {
      // Validate drop
      let isValid = true;

      if (this.options.validateDrop) {
        isValid = this.options.validateDrop(this.state.fromSquare, dropSquare);
      }

      if (isValid && this.options.onDrop) {
        // Try to drop the piece
        const success = await this.options.onDrop(
          this.state.fromSquare,
          dropSquare,
          this.state.piece
        );

        if (!success) {
          // Drop failed, restore original piece
          this.restoreOriginalPiece();
        }
      } else {
        // Invalid drop, restore original piece
        this.restoreOriginalPiece();
      }
    } else {
      // Dropped on invalid square or same square, restore
      this.restoreOriginalPiece();
    }

    // Reset state
    this.resetState();
  }

  /**
   * Handle drag cancel
   */
  private handleCancel(data: PointerEventData): void {
    if (!this.state.active) return;

    // Clean up
    this.cleanupDragElement();
    this.restoreOriginalPiece();

    // Call callback
    if (this.options.onDragCancel) {
      this.options.onDragCancel();
    }

    // Reset state
    this.resetState();
  }

  /**
   * Create drag element (ghost piece)
   */
  private createDragElement(piece: Piece): HTMLElement {
    const element = document.createElement('div');
    element.className = 'piece-drag-ghost';
    element.style.cssText = `
      position: fixed;
      pointer-events: none;
      z-index: 10000;
      font-size: 3em;
      opacity: 0.8;
      transform: translate(-50%, -50%);
      user-select: none;
    `;

    // Use same piece symbol
    const symbols: Record<string, string> = {
      pawn: piece.color === 'white' ? '♙' : '♟',
      knight: piece.color === 'white' ? '♘' : '♞',
      bishop: piece.color === 'white' ? '♗' : '♝',
      rook: piece.color === 'white' ? '♖' : '♜',
      queen: piece.color === 'white' ? '♕' : '♛',
      king: piece.color === 'white' ? '♔' : '♚',
    };

    element.textContent = symbols[piece.type] || '';

    return element;
  }

  /**
   * Update drag element position
   */
  private updateDragElementPosition(x: number, y: number): void {
    if (!this.state.dragElement) return;

    this.state.dragElement.style.left = `${x}px`;
    this.state.dragElement.style.top = `${y}px`;
  }

  /**
   * Get square at screen position
   */
  private getSquareAtPosition(x: number, y: number): Square | null {
    if (!this.boardRect) return null;

    // Convert screen coordinates to board coordinates
    const relX = x - this.boardRect.left;
    const relY = y - this.boardRect.top;

    // Check if within board bounds
    if (relX < 0 || relX >= this.boardRect.width || relY < 0 || relY >= this.boardRect.height) {
      return null;
    }

    // Calculate square
    const file = Math.floor(relX / this.squareSize);
    const rank = Math.floor((this.boardRect.height - relY) / this.squareSize);

    if (file < 0 || file > 7 || rank < 0 || rank > 7) {
      return null;
    }

    return { file, rank };
  }

  /**
   * Highlight legal move squares
   */
  private highlightLegalSquares(): void {
    this.clearSquareHighlight();

    this.state.legalSquares.forEach((square) => {
      const squareElement = this.getSquareElement(square);
      if (squareElement) {
        squareElement.classList.add('legal-move');
      }
    });
  }

  /**
   * Update square highlight during drag
   */
  private updateSquareHighlight(square: Square): void {
    // Remove previous hover highlight
    const prevHover = this.boardElement.querySelector('.square.hover');
    if (prevHover) {
      prevHover.classList.remove('hover');
    }

    // Add hover highlight to current square
    const squareElement = this.getSquareElement(square);
    if (squareElement) {
      squareElement.classList.add('hover');
    }
  }

  /**
   * Clear square highlight
   */
  private clearSquareHighlight(): void {
    const highlightedSquares = this.boardElement.querySelectorAll('.square.legal-move, .square.hover');
    highlightedSquares.forEach((el) => {
      el.classList.remove('legal-move', 'hover');
    });
  }

  /**
   * Get square element
   */
  private getSquareElement(square: Square): HTMLElement | null {
    const squares = this.boardElement.querySelectorAll('.square');
    for (let i = 0; i < squares.length; i++) {
      const el = squares[i] as HTMLElement;
      const file = parseInt(el.dataset.file || '0');
      const rank = parseInt(el.dataset.rank || '0');

      if (file === square.file && rank === square.rank) {
        return el;
      }
    }
    return null;
  }

  /**
   * Clean up drag element
   */
  private cleanupDragElement(): void {
    if (this.state.dragElement) {
      this.state.dragElement.remove();
      this.state.dragElement = null;
    }

    this.boardElement.classList.remove('piece-dragging');
    this.clearSquareHighlight();
  }

  /**
   * Restore original piece visibility
   */
  private restoreOriginalPiece(): void {
    if (this.state.originalElement) {
      this.state.originalElement.style.opacity = '';
    }
  }

  /**
   * Reset drag state
   */
  private resetState(): void {
    this.state = {
      active: false,
      piece: null,
      fromSquare: null,
      currentSquare: null,
      startX: 0,
      startY: 0,
      dragElement: null,
      originalElement: null,
      legalSquares: [],
    };
  }

  /**
   * Check if currently dragging
   */
  public isDragging(): boolean {
    return this.state.active;
  }

  /**
   * Get drag state
   */
  public getState(): DragState {
    return { ...this.state };
  }

  /**
   * Destroy and cleanup
   */
  public destroy(): void {
    this.cleanupDragElement();
    this.resetState();
    this.unsubscribers.forEach((unsub) => unsub());
    this.unsubscribers = [];
  }
}
