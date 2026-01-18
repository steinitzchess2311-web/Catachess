/**
 * Chessboard Module
 *
 * Complete chessboard component with drag-and-drop, move validation,
 * and backend integration.
 *
 * IMPORTANT: All chess rules and move validation are handled by the backend.
 * This module only provides UI interactions.
 */

// Export main component
export { Chessboard, createChessboard } from './components/Chessboard';

// Export piece dragger (uses core drag system)
export { PieceDragger } from './components/PieceDragger';
export type { PieceDragOptions, DragState as PieceDragState } from './components/PieceDragger';

// Export types
export type {
  Color,
  PieceType,
  Piece,
  Square,
  Move,
  BoardPosition,
  ChessboardState,
  ChessboardOptions,
  DragState,
} from './types';

// Export utilities
export {
  squareToAlgebraic,
  algebraicToSquare,
  squaresEqual,
  squareToIndex,
  indexToSquare,
  getPieceSymbol,
  createInitialPosition,
} from './types';

// Export API client
export { ChessAPI, chessAPI } from './utils/api';

// Export storage (auto-save system)
export { GameStorage, createGameStorage } from './storage';
export type { GameInfo, SaveMoveOptions, GameStorageOptions } from './storage';

// Export engine analysis
export { EngineAnalysis, createEngineAnalysis } from './components/EngineAnalysis';
export type { EngineAnalysisOptions } from './components/EngineAnalysis';
export { ImitatorPanel, createImitatorPanel } from './components/ImitatorPanel';
export type {
  EngineLine,
  EngineAnalysisResult,
  EngineSpotMetrics,
  EngineHealthInfo,
} from './utils/api';
