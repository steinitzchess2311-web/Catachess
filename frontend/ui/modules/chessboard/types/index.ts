/**
 * Chessboard Types
 *
 * Type definitions for chess board, pieces, and moves.
 */

export type Color = 'white' | 'black';

export type PieceType = 'pawn' | 'knight' | 'bishop' | 'rook' | 'queen' | 'king';

export interface Piece {
  color: Color;
  type: PieceType;
}

export interface Square {
  file: number; // 0-7 (a-h)
  rank: number; // 0-7 (1-8)
}

export interface Move {
  from: Square;
  to: Square;
  promotion?: PieceType;
  piece?: Piece;
  captured?: Piece;
  isCheck?: boolean;
  isCheckmate?: boolean;
  isCastling?: boolean;
  isEnPassant?: boolean;
}

export interface BoardPosition {
  // Board layout: 8x8 array, null represents empty square
  squares: (Piece | null)[][];
  turn: Color;
  castlingRights: {
    whiteKingside: boolean;
    whiteQueenside: boolean;
    blackKingside: boolean;
    blackQueenside: boolean;
  };
  enPassantSquare: Square | null;
  halfmoveClock: number;
  fullmoveNumber: number;
}

export interface ChessboardState {
  position: BoardPosition;
  selectedSquare: Square | null;
  legalMoves: Move[];
  highlightedSquares: Square[];
  lastMove: Move | null;
  isFlipped: boolean;
  isDragging: boolean;
  draggedPiece: { piece: Piece; from: Square } | null;
}

export interface ChessboardOptions {
  initialPosition?: BoardPosition;
  orientation?: Color;
  draggable?: boolean;
  selectable?: boolean;
  showCoordinates?: boolean;
  showLegalMoves?: boolean;
  highlightLastMove?: boolean;
  enableStorage?: boolean; // Enable auto-save to backend
  gameId?: string; // Game ID for storage
  onMove?: (move: Move) => void;
  onPieceSelect?: (square: Square, piece: Piece) => void;
  onSquareClick?: (square: Square) => void;
  validateMove?: (move: Move) => Promise<boolean>;
  onSaved?: (gameId: string) => void; // Called after move is saved
  onStorageError?: (error: Error) => void;
}

export interface DragState {
  piece: Piece;
  from: Square;
  startX: number;
  startY: number;
  currentX: number;
  currentY: number;
}

/**
 * Convert square to algebraic notation (e.g., 'e4')
 */
export function squareToAlgebraic(square: Square): string {
  const files = 'abcdefgh';
  return files[square.file] + (square.rank + 1);
}

/**
 * Convert algebraic notation to square
 */
export function algebraicToSquare(notation: string): Square {
  const files = 'abcdefgh';
  const file = files.indexOf(notation[0]);
  const rank = parseInt(notation[1]) - 1;
  return { file, rank };
}

/**
 * Check if two squares are equal
 */
export function squaresEqual(a: Square | null, b: Square | null): boolean {
  if (!a || !b) return false;
  return a.file === b.file && a.rank === b.rank;
}

/**
 * Get square index (0-63)
 */
export function squareToIndex(square: Square): number {
  return square.rank * 8 + square.file;
}

/**
 * Get square from index (0-63)
 */
export function indexToSquare(index: number): Square {
  return {
    file: index % 8,
    rank: Math.floor(index / 8),
  };
}

/**
 * Get piece symbol for display
 */
export function getPieceSymbol(piece: Piece): string {
  const symbols: Record<PieceType, string> = {
    pawn: '♟',
    knight: '♞',
    bishop: '♝',
    rook: '♜',
    queen: '♛',
    king: '♚',
  };

  const symbol = symbols[piece.type];
  return piece.color === 'white' ? symbol.replace('♟', '♙').replace('♞', '♘').replace('♝', '♗').replace('♜', '♖').replace('♛', '♕').replace('♚', '♔') : symbol;
}

/**
 * Create initial chess position
 */
export function createInitialPosition(): BoardPosition {
  const squares: (Piece | null)[][] = Array(8)
    .fill(null)
    .map(() => Array(8).fill(null));

  // Setup white pieces
  squares[0][0] = { color: 'white', type: 'rook' };
  squares[0][1] = { color: 'white', type: 'knight' };
  squares[0][2] = { color: 'white', type: 'bishop' };
  squares[0][3] = { color: 'white', type: 'queen' };
  squares[0][4] = { color: 'white', type: 'king' };
  squares[0][5] = { color: 'white', type: 'bishop' };
  squares[0][6] = { color: 'white', type: 'knight' };
  squares[0][7] = { color: 'white', type: 'rook' };

  for (let i = 0; i < 8; i++) {
    squares[1][i] = { color: 'white', type: 'pawn' };
  }

  // Setup black pieces
  squares[7][0] = { color: 'black', type: 'rook' };
  squares[7][1] = { color: 'black', type: 'knight' };
  squares[7][2] = { color: 'black', type: 'bishop' };
  squares[7][3] = { color: 'black', type: 'queen' };
  squares[7][4] = { color: 'black', type: 'king' };
  squares[7][5] = { color: 'black', type: 'bishop' };
  squares[7][6] = { color: 'black', type: 'knight' };
  squares[7][7] = { color: 'black', type: 'rook' };

  for (let i = 0; i < 8; i++) {
    squares[6][i] = { color: 'black', type: 'pawn' };
  }

  return {
    squares,
    turn: 'white',
    castlingRights: {
      whiteKingside: true,
      whiteQueenside: true,
      blackKingside: true,
      blackQueenside: true,
    },
    enPassantSquare: null,
    halfmoveClock: 0,
    fullmoveNumber: 1,
  };
}
