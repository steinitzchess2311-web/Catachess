/**
 * Chessboard Storage Module
 *
 * Manages game storage by triggering backend APIs.
 * All PGN logic, variations, and R2 storage are handled by backend.
 */

export { GameStorage, createGameStorage } from './GameStorage';
export type { GameInfo, SaveMoveOptions, GameStorageOptions } from './GameStorage';
