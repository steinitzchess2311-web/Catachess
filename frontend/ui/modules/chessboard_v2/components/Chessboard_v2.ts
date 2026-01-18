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
} from '../types'; // Assuming types are in the parent directory for now
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

export class ChessboardV2 {
  private container: HTMLElement;
  private boardElement: HTMLElement;
  private options: Required<ChessboardOptions>;
  private state: ChessboardState;

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
  }

  private render(): void {
    this.container.innerHTML = '';
    this.container.style.position = 'relative';
    this.container.style.width = '100%';
    this.container.style.aspectRatio = '1';

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
    pieceElement.draggable = true;
    pieceElement.dataset.color = piece.color;
    pieceElement.dataset.type = piece.type;
    pieceElement.dataset.square = squareToAlgebraic(square);
    return pieceElement;
  }

  private setupEventListeners(): void {
    this.boardElement.addEventListener('dragstart', this.handleDragStart.bind(this));
    this.boardElement.addEventListener('dragover', this.handleDragOver.bind(this));
    this.boardElement.addEventListener('drop', this.handleDrop.bind(this));
  }

  private handleDragStart(e: DragEvent): void {
    const target = e.target as HTMLElement;
    if (!target.classList.contains('piece')) return;

    const square = target.parentElement as HTMLElement;
    const from = {
      file: parseInt(square.dataset.file!, 10),
      rank: parseInt(square.dataset.rank!, 10),
    };

    e.dataTransfer!.setData('text/plain', JSON.stringify(from));
    e.dataTransfer!.effectAllowed = 'move';
    
    // For visual feedback
    setTimeout(() => {
        target.style.opacity = '0.5';
    }, 0);
  }

  private handleDragOver(e: DragEvent): void {
    e.preventDefault();
    e.dataTransfer!.dropEffect = 'move';
  }

  private async handleDrop(e: DragEvent): Promise<void> {
    e.preventDefault();
    const fromSquare = JSON.parse(e.dataTransfer!.getData('text/plain'));
    const target = e.target as HTMLElement;
    const toSquareEl = target.closest('.square') as HTMLElement;

    const fromEl = this.boardElement.querySelector(`.square[data-file='${fromSquare.file}'][data-rank='${fromSquare.rank}']`) as HTMLElement;
    const pieceEl = fromEl.querySelector('.piece') as HTMLElement;
    if (pieceEl) {
        pieceEl.style.opacity = '1';
    }

    if (!toSquareEl) return;
    
    const to = {
      file: parseInt(toSquareEl.dataset.file!, 10),
      rank: parseInt(toSquareEl.dataset.rank!, 10),
    };

    if (squaresEqual(fromSquare, to)) return;

    const move: Move = { from: fromSquare, to };
    const success = await this.makeMove(move);

    if (success) {
      this.options.onMove(move);
    } else {
      // If move is not successful, snap back. The re-render will handle this.
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
        cursor: grab;
      }
      .change-pieces-btn {
        position: absolute;
        top: -30px;
        right: 0;
        z-index: 10;
      }
      .chessboard-v2 .square.drag-over {
        background-color: rgba(255, 255, 0, 0.5);
      }
    `;
    document.head.appendChild(style);
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
    this.container.innerHTML = '';
  }
}
