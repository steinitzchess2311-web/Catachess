/**
 * Game Storage Manager
 *
 * Frontend storage manager that triggers backend to save game state.
 * All PGN logic, variation handling, and R2 storage are done by backend.
 *
 * Frontend responsibility: Trigger save events only
 * Backend responsibility: PGN generation, variation branches, R2 storage
 */

import { Move, BoardPosition } from '../types';
import { chessAPI } from '../utils/api';

export interface GameInfo {
  gameId: string;
  playerWhite?: string;
  playerBlack?: string;
  event?: string;
  site?: string;
  date?: string;
  round?: string;
}

export interface SaveMoveOptions {
  gameId: string;
  move: Move;
  position: BoardPosition;
  isVariation?: boolean; // Is this move part of a variation branch?
  parentMoveId?: string; // Parent move ID for variation
  comment?: string;
  nag?: number; // Numeric Annotation Glyph (!, ?, !!, ??, etc.)
}

export interface GameStorageOptions {
  autoSave?: boolean; // Auto-save after each move
  gameInfo?: GameInfo;
  onSaved?: (gameId: string) => void;
  onError?: (error: Error) => void;
}

/**
 * Game storage manager - triggers backend to save game state
 */
export class GameStorage {
  private options: Required<GameStorageOptions>;
  private gameId: string | null = null;
  private moveCount: number = 0;

  constructor(options: GameStorageOptions = {}) {
    this.options = {
      autoSave: options.autoSave !== false,
      gameInfo: options.gameInfo || {
        gameId: this.generateGameId(),
        event: 'Casual Game',
        site: 'Catachess',
        date: new Date().toISOString().split('T')[0],
      },
      onSaved: options.onSaved || (() => {}),
      onError: options.onError || ((error) => console.error('Storage error:', error)),
    };

    this.gameId = this.options.gameInfo.gameId;
  }

  /**
   * Generate unique game ID
   */
  private generateGameId(): string {
    return `game_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Save move to backend (triggers PGN save + R2 storage)
   */
  public async saveMove(options: SaveMoveOptions): Promise<boolean> {
    try {
      // Call backend API to save move
      // Backend will:
      // 1. Update PGN with new move
      // 2. Handle variation branches if isVariation=true
      // 3. Store to R2 database
      const response = await fetch(`${chessAPI['baseURL']}/api/games/save-move`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          game_id: options.gameId,
          move: {
            from: {
              file: options.move.from.file,
              rank: options.move.from.rank,
            },
            to: {
              file: options.move.to.file,
              rank: options.move.to.rank,
            },
            promotion: options.move.promotion,
          },
          position_fen: this.positionToFEN(options.position),
          is_variation: options.isVariation || false,
          parent_move_id: options.parentMoveId,
          comment: options.comment,
          nag: options.nag,
          move_number: this.moveCount + 1,
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to save move: ${response.statusText}`);
      }

      const data = await response.json();

      this.moveCount++;
      this.options.onSaved(this.gameId!);

      return true;
    } catch (error) {
      this.options.onError(error as Error);
      return false;
    }
  }

  /**
   * Start a new variation branch
   */
  public async startVariation(parentMoveId: string): Promise<boolean> {
    try {
      // Notify backend to start a new variation branch
      const response = await fetch(`${chessAPI['baseURL']}/api/games/start-variation`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          game_id: this.gameId,
          parent_move_id: parentMoveId,
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to start variation: ${response.statusText}`);
      }

      return true;
    } catch (error) {
      this.options.onError(error as Error);
      return false;
    }
  }

  /**
   * End current variation branch
   */
  public async endVariation(): Promise<boolean> {
    try {
      // Notify backend to end current variation
      const response = await fetch(`${chessAPI['baseURL']}/api/games/end-variation`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          game_id: this.gameId,
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to end variation: ${response.statusText}`);
      }

      return true;
    } catch (error) {
      this.options.onError(error as Error);
      return false;
    }
  }

  /**
   * Add comment to last move
   */
  public async addComment(comment: string, moveId?: string): Promise<boolean> {
    try {
      const response = await fetch(`${chessAPI['baseURL']}/api/games/add-comment`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          game_id: this.gameId,
          move_id: moveId,
          comment: comment,
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to add comment: ${response.statusText}`);
      }

      return true;
    } catch (error) {
      this.options.onError(error as Error);
      return false;
    }
  }

  /**
   * Add NAG (Numeric Annotation Glyph) to last move
   */
  public async addNAG(nag: number, moveId?: string): Promise<boolean> {
    try {
      const response = await fetch(`${chessAPI['baseURL']}/api/games/add-nag`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          game_id: this.gameId,
          move_id: moveId,
          nag: nag,
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to add NAG: ${response.statusText}`);
      }

      return true;
    } catch (error) {
      this.options.onError(error as Error);
      return false;
    }
  }

  /**
   * Get game PGN from backend
   */
  public async getPGN(): Promise<string> {
    try {
      const response = await fetch(
        `${chessAPI['baseURL']}/api/games/${this.gameId}/pgn`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to get PGN: ${response.statusText}`);
      }

      const data = await response.json();
      return data.pgn || '';
    } catch (error) {
      this.options.onError(error as Error);
      return '';
    }
  }

  /**
   * Load game from backend
   */
  public async loadGame(gameId: string): Promise<boolean> {
    try {
      const response = await fetch(`${chessAPI['baseURL']}/api/games/${gameId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to load game: ${response.statusText}`);
      }

      const data = await response.json();
      this.gameId = gameId;
      this.moveCount = data.move_count || 0;

      return true;
    } catch (error) {
      this.options.onError(error as Error);
      return false;
    }
  }

  /**
   * Delete game from backend
   */
  public async deleteGame(): Promise<boolean> {
    try {
      const response = await fetch(`${chessAPI['baseURL']}/api/games/${this.gameId}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to delete game: ${response.statusText}`);
      }

      return true;
    } catch (error) {
      this.options.onError(error as Error);
      return false;
    }
  }

  /**
   * Get game ID
   */
  public getGameId(): string | null {
    return this.gameId;
  }

  /**
   * Get move count
   */
  public getMoveCount(): number {
    return this.moveCount;
  }

  /**
   * Set auto-save enabled/disabled
   */
  public setAutoSave(enabled: boolean): void {
    this.options.autoSave = enabled;
  }

  /**
   * Is auto-save enabled?
   */
  public isAutoSaveEnabled(): boolean {
    return this.options.autoSave;
  }

  /**
   * Convert position to FEN (helper)
   */
  private positionToFEN(position: BoardPosition): string {
    // This is a simplified version - same as in api.ts
    let fen = '';

    // Board layout
    for (let rank = 7; rank >= 0; rank--) {
      let emptyCount = 0;

      for (let file = 0; file < 8; file++) {
        const piece = position.squares[rank][file];

        if (piece === null) {
          emptyCount++;
        } else {
          if (emptyCount > 0) {
            fen += emptyCount;
            emptyCount = 0;
          }

          const pieceChars: Record<string, string> = {
            pawn: 'p',
            knight: 'n',
            bishop: 'b',
            rook: 'r',
            queen: 'q',
            king: 'k',
          };

          const char = pieceChars[piece.type];
          fen += piece.color === 'white' ? char.toUpperCase() : char;
        }
      }

      if (emptyCount > 0) {
        fen += emptyCount;
      }

      if (rank > 0) {
        fen += '/';
      }
    }

    // Active color
    fen += ' ' + (position.turn === 'white' ? 'w' : 'b');

    // Castling rights
    let castling = '';
    if (position.castlingRights.whiteKingside) castling += 'K';
    if (position.castlingRights.whiteQueenside) castling += 'Q';
    if (position.castlingRights.blackKingside) castling += 'k';
    if (position.castlingRights.blackQueenside) castling += 'q';
    fen += ' ' + (castling || '-');

    // En passant
    if (position.enPassantSquare) {
      const files = 'abcdefgh';
      fen += ' ' + files[position.enPassantSquare.file] + (position.enPassantSquare.rank + 1);
    } else {
      fen += ' -';
    }

    // Halfmove clock and fullmove number
    fen += ' ' + position.halfmoveClock + ' ' + position.fullmoveNumber;

    return fen;
  }
}

/**
 * Create a game storage instance
 */
export function createGameStorage(options?: GameStorageOptions): GameStorage {
  return new GameStorage(options);
}
