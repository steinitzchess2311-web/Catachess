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
    this.container.style.aspectRatio = '1 / 1';

    const changePiecesButton = document.createElement('button');
    changePiecesButton.textContent = `Pieces: ${getCurrentPieceSet().name}`;
    changePiecesButton.className = 'change-pieces-btn';
    changePiecesButton.addEventListener('click', () => {
      nextPieceSet();
      this.render();
    });
    this.container.appendChild(changePiecesButton);

    this.boardElement.className = 'chessboard-v2';
    this.boardElement.innerHTML = '';

    for (let rank = 7; rank >= 0; rank--) {
      for (let file = 0; file < 8; file++) {
        const squareData = { file, rank };
        const squareElement = this.createSquareElement(squareData);
        this.boardElement.appendChild(squareElement);
      }
    }
    this.container.appendChild(this.boardElement);
    this.syncSquareSize();
  }

  private createSquareElement(square: Square): HTMLElement {
    const squareElement = document.createElement('div');
    squareElement.className = 'square';
    squareElement.dataset.file = String(square.file);
    squareElement.dataset.rank = String(square.rank);

    const isLight = (square.file + square.rank) % 2 !== 0;
    squareElement.classList.add(isLight ? 'light' : 'dark');
    
    const piece = this.state.position.squares[square.rank][square.file];
    if (piece) {
      const pieceElement = this.createPieceElement(piece, square);
      squareElement.appendChild(pieceElement);
    }

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

    const square = {
      file: parseInt(squareElement.dataset.file || '0', 10),
      rank: parseInt(squareElement.dataset.rank || '0', 10),
    };

    this.options.onSquareClick(square);

    const piece = this.state.position.squares[square.rank][square.file];

    if (piece && piece.color === this.state.position.turn) {
      this.state.selectedSquare = square;
      this.state.legalMoves = await chessAPI.getLegalMoves(this.state.position, square);
      this.options.onPieceSelect(square, piece);
      return;
    }

    if (!this.state.selectedSquare) return;

    const move: Move = { from: this.state.selectedSquare, to: square };
    const success = await this.makeMove(move);

    this.state.selectedSquare = null;
    this.state.legalMoves = [];

    if (success) {
      this.options.onMove(move);
    } else {
      this.render();
    }
  }

  private async makeMove(move: Move): Promise<boolean> {
    const isValid = await this.options.validateMove(move);
    if (!isValid) {
      return false;
    }

    try {
      const result = await chessAPI.applyMove(this.state.position, move);
      this.state.position = result.position;
      this.state.lastMove = move;
      this.render();
      return true;
    } catch (error) {
      console.error("Failed to apply move:", error);
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
        height: 100%;
        user-select: none;
      }
      .chessboard-v2 .square {
        position: relative;
      }
      .chessboard-v2 .square.light { background-color: #f0d9b5; }
      .chessboard-v2 .square.dark { background-color: #b58863; }
      .chessboard-v2 .piece {
        width: 100%;
        height: 100%;
        object-fit: contain;
        cursor: default;
        -webkit-user-drag: none;
        -webkit-user-select: none;
        pointer-events: none;
        touch-action: none;
      }
      .change-pieces-btn {
        position: absolute;
        top: -30px;
        right: 0;
        z-index: 10;
      }
    `;
    document.head.appendChild(style);
  }

  private setupResizeHandling(): void {
    const target = this.container.parentElement || this.container;
    this.syncSquareSize();

    if (typeof ResizeObserver !== 'undefined') {
      this.resizeObserver = new ResizeObserver(() => {
        this.syncSquareSize();
      });
      this.resizeObserver.observe(target);
      return;
    }

    this.resizeHandler = () => this.syncSquareSize();
    window.addEventListener('resize', this.resizeHandler);
  }

  private syncSquareSize(): void {
    const parent = this.container.parentElement;
    const target = parent || this.container;
    const bounds = target.getBoundingClientRect();

    let availableWidth = bounds.width;
    let availableHeight = bounds.height;

    if (parent) {
      const styles = getComputedStyle(parent);
      const paddingX =
        parseFloat(styles.paddingLeft || '0') + parseFloat(styles.paddingRight || '0');
      const paddingY =
        parseFloat(styles.paddingTop || '0') + parseFloat(styles.paddingBottom || '0');
      const gapValue = styles.rowGap || styles.gap || '0';
      const gap = parseFloat(gapValue || '0') || 0;
      const controls = parent.querySelector('.board-controls') as HTMLElement | null;
      let controlsHeight = 0;
      if (controls) {
        const controlsStyles = getComputedStyle(controls);
        const margins =
          parseFloat(controlsStyles.marginTop || '0') +
          parseFloat(controlsStyles.marginBottom || '0');
        controlsHeight = controls.getBoundingClientRect().height + margins;
      }

      availableWidth = Math.max(0, availableWidth - paddingX);
      availableHeight = Math.max(0, availableHeight - paddingY - controlsHeight - gap);
    }

    const maxSize = Math.min(availableWidth, availableHeight);
    if (maxSize > 0) {
      this.container.style.width = `${maxSize}px`;
      this.container.style.height = `${maxSize}px`;
    }
  }

  public flip(): void {
    this.state.isFlipped = !this.state.isFlipped;
    this.render();
  }

  public setPosition(position: BoardPosition): void {
    this.state.position = position;
    this.render();
  }

  public getPosition(): BoardPosition {
    return this.state.position;
  }

  public reset(): void {
    this.state.position = createInitialPosition();
    this.render();
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
