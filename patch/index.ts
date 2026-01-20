// Patch module barrel exports

// Context
export { StudyProvider, useStudy } from './studyContext';
export type {
  StudyState,
  StudyContextValue,
  StudyError,
  StudyErrorType,
} from './studyContext';

// Board
export { StudyBoard } from './board/studyBoard';
export type { StudyBoardProps } from './board/studyBoard';

// Tree types and constants
export {
  TREE_SCHEMA_VERSION,
  validateTree,
} from './tree/type';
export type {
  StudyNode,
  StudyTree as StudyTreeData,
  TreeMeta,
  TreeCursor,
  TreeOperation,
  TreeValidationResult,
} from './tree/type';

// Tree class and utilities
export { StudyTree, createEmptyTree } from './tree/StudyTree';

// Cursor utilities
export {
  createCursor,
  createCursorAt,
  getCursorNodeId,
  getCursorNode,
  getCursorPath,
  moveCursorToParent,
  moveCursorToMainline,
  moveCursorToVariation,
  isAtRoot,
  isAtLeaf,
} from './tree/cursor';

// PGN (placeholder functions)
export { parsePgn, detectGames, parseMultiplePgn } from './pgn/import';
export { exportToPgn, exportMainlineToPgn, formatPgnHeaders } from './pgn/export';

// Chess.js replay utilities
export {
  STARTING_FEN,
  replaySanPath,
  validateMove,
  getValidMoves,
  createReplayState,
  replayMove,
  replayMoves,
} from './chessJS/replay';
export type {
  ReplayResult,
  ValidateMoveResult,
  CreateReplayStateResult,
  ReplayMoveResult,
  ReplayMovesResult,
} from './chessJS/replay';

// FEN utilities
export {
  fenFromPath,
  parseFen,
  validateFen,
  composeFen,
  isStartingPosition,
  getTurn,
  getFullmoveNumber,
  getHalfmoveClock,
} from './chessJS/fen';
export type { FenFromPathResult, FenParts, FenValidationResult } from './chessJS/fen';

// Sidebar
export { MoveTree } from './sidebar/movetree';
export type { MoveTreeProps } from './sidebar/movetree';

// Pages
export { PatchStudyPage } from './PatchStudyPage';
export type { PatchStudyPageProps } from './PatchStudyPage';
