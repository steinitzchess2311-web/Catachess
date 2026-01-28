/**
 * CataMaze Terminal Module - Main Exports
 * For integration with CataChess terminal system
 */

// Main component
export { CataMazeTerminal, CataMazeTerminal as default } from './CataMazeTerminal';

// Types
export type { Observation, GameStateResponse } from './apiClient';

// For direct command integration
export { createCataMazeCommand } from './commands/catamaze';
