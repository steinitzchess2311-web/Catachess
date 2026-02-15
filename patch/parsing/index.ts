/**
 * Parsing Module - Main Entry Point
 *
 * Export all parsing functionality for FEN and PGN imports.
 * Created: 2025-02-15
 */

// FEN Import
export {
  importFromFen,
  quickValidateFen,
  getPositionInfo,
  FEN_TEMPLATES,
  STANDARD_STARTING_FEN,
  isStandardStartingFen,
} from './fen_import';

// Validators
export {
  validateFen,
  parseFenComponents,
  isStandardPosition,
  normalizeFen,
  getFriendlyFenError,
  isPlayableFen,
} from './validators';

// Types
export type {
  ParseResult,
  FenValidation,
  FenComponents,
  ParseOptions,
  PgnMetadata,
} from './types';

export { isParseSuccess } from './types';
