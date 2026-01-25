/**
 * Chess API Client
 *
 * Communicates with backend chess engine for move validation and game logic.
 */

import { Move, BoardPosition, Square, Piece } from '../types';

function resolveApiBase(): string {
  const envBase = import.meta.env.VITE_API_BASE as string | undefined;
  if (envBase) return envBase;
  const host = window.location.hostname;
  if (host === 'localhost' || host === '127.0.0.1') {
    return 'http://localhost:8000';
  }
  return 'https://api.catachess.com';
}

const API_BASE_URL = resolveApiBase();

/**
 * Convert frontend move to backend format
 */
function moveToBackendFormat(move: Move) {
  return {
    from_square: {
      file: move.from.file,
      rank: move.from.rank,
    },
    to_square: {
      file: move.to.file,
      rank: move.to.rank,
    },
    promotion: move.promotion || null,
  };
}

/**
 * Convert backend position to frontend format
 */
function boardPositionFromBackend(data: any): BoardPosition {
  if (data?.fen) {
    return fenToBoardPosition(data.fen);
  }
  return createEmptyPosition(data);
}

function createEmptyPosition(data: any): BoardPosition {
  const squares: (Piece | null)[][] = Array(8)
    .fill(null)
    .map(() => Array(8).fill(null));

  return {
    squares,
    turn: data?.turn || 'white',
    castlingRights: data?.castling_rights || {
      whiteKingside: true,
      whiteQueenside: true,
      blackKingside: true,
      blackQueenside: true,
    },
    enPassantSquare: data?.en_passant_square || null,
    halfmoveClock: data?.halfmove_clock || 0,
    fullmoveNumber: data?.fullmove_number || 1,
  };
}

export function fenToBoardPosition(fen: string): BoardPosition {
  const parts = fen.trim().split(/\s+/);
  if (parts.length < 4) {
    throw new Error('Invalid FEN string');
  }

  const boardPart = parts[0];
  const turnPart = parts[1];
  const castlingPart = parts[2];
  const enPassantPart = parts[3];
  const halfmoveClock = Number(parts[4] || 0);
  const fullmoveNumber = Number(parts[5] || 1);

  const squares: (Piece | null)[][] = Array(8)
    .fill(null)
    .map(() => Array(8).fill(null));

  const ranks = boardPart.split('/');
  if (ranks.length !== 8) {
    throw new Error('Invalid FEN board');
  }

  ranks.forEach((rankText, fenRankIndex) => {
    let fileIndex = 0;
    for (const char of rankText) {
      if (/\d/.test(char)) {
        fileIndex += Number(char);
        continue;
      }
      const color = char === char.toUpperCase() ? 'white' : 'black';
      const lower = char.toLowerCase();
      const type =
        lower === 'p'
          ? 'pawn'
          : lower === 'n'
            ? 'knight'
            : lower === 'b'
              ? 'bishop'
              : lower === 'r'
                ? 'rook'
                : lower === 'q'
                  ? 'queen'
                  : 'king';

      const rankIndex = 7 - fenRankIndex;
      squares[rankIndex][fileIndex] = { color, type };
      fileIndex += 1;
    }
  });

  const castlingRights = {
    whiteKingside: castlingPart.includes('K'),
    whiteQueenside: castlingPart.includes('Q'),
    blackKingside: castlingPart.includes('k'),
    blackQueenside: castlingPart.includes('q'),
  };

  let enPassantSquare: Square | null = null;
  if (enPassantPart !== '-') {
    const files = 'abcdefgh';
    const file = files.indexOf(enPassantPart[0]);
    const rank = Number(enPassantPart[1]) - 1;
    if (file >= 0 && rank >= 0) {
      enPassantSquare = { file, rank };
    }
  }

  return {
    squares,
    turn: turnPart === 'b' ? 'black' : 'white',
    castlingRights,
    enPassantSquare,
    halfmoveClock: Number.isNaN(halfmoveClock) ? 0 : halfmoveClock,
    fullmoveNumber: Number.isNaN(fullmoveNumber) ? 1 : fullmoveNumber,
  };
}

/**
 * Chess API Client
 */
export class ChessAPI {
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  private buildHeaders() {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    const token =
      localStorage.getItem('catachess_token') ||
      sessionStorage.getItem('catachess_token');
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
  }

  /**
   * Validate if a move is legal
   */
  async validateMove(position: BoardPosition, move: Move): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseURL}/api/chess/validate-move`, {
        method: 'POST',
        headers: this.buildHeaders(),
        body: JSON.stringify({
          position: this.positionToFEN(position),
          move: moveToBackendFormat(move),
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data.is_legal || false;
    } catch (error) {
      console.error('Failed to validate move:', error);
      // Fallback to client-side validation if backend is unavailable
      return this.clientSideValidation(position, move);
    }
  }

  /**
   * Get all legal moves for current position
   */
  async getLegalMoves(position: BoardPosition, square?: Square): Promise<Move[]> {
    try {
      const response = await fetch(`${this.baseURL}/api/chess/legal-moves`, {
        method: 'POST',
        headers: this.buildHeaders(),
        body: JSON.stringify({
          position: this.positionToFEN(position),
          square: square ? { file: square.file, rank: square.rank } : null,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data.legal_moves || [];
    } catch (error) {
      console.error('Failed to get legal moves:', error);
      return [];
    }
  }

  /**
   * Apply move and get new position
   */
  async applyMove(
    position: BoardPosition,
    move: Move,
  ): Promise<{ position: BoardPosition; moveMeta?: Record<string, unknown> }> {
    try {
      const response = await fetch(`${this.baseURL}/api/chess/apply-move`, {
        method: 'POST',
        headers: this.buildHeaders(),
        body: JSON.stringify({
          position: this.positionToFEN(position),
          move: moveToBackendFormat(move),
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return {
        position: boardPositionFromBackend(data.new_position),
        moveMeta: data.move || undefined,
      };
    } catch (error) {
      console.error('Failed to apply move:', error);
      throw error;
    }
  }

  /**
   * Check if position is in check
   */
  async isInCheck(position: BoardPosition): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseURL}/api/chess/is-check`, {
        method: 'POST',
        headers: this.buildHeaders(),
        body: JSON.stringify({
          position: this.positionToFEN(position),
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data.is_check || false;
    } catch (error) {
      console.error('Failed to check if in check:', error);
      return false;
    }
  }

  /**
   * Check if position is checkmate
   */
  async isCheckmate(position: BoardPosition): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseURL}/api/chess/is-checkmate`, {
        method: 'POST',
        headers: this.buildHeaders(),
        body: JSON.stringify({
          position: this.positionToFEN(position),
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data.is_checkmate || false;
    } catch (error) {
      console.error('Failed to check if checkmate:', error);
      return false;
    }
  }

  /**
   * Convert board position to FEN string
   */
  private positionToFEN(position: BoardPosition): string {
    // Convert board position to FEN notation
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

          const pieceChar = this.pieceToChar(piece);
          fen += pieceChar;
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
      fen +=
        ' ' +
        files[position.enPassantSquare.file] +
        (position.enPassantSquare.rank + 1);
    } else {
      fen += ' -';
    }

    // Halfmove clock and fullmove number
    fen += ' ' + position.halfmoveClock + ' ' + position.fullmoveNumber;

    return fen;
  }

  /**
   * Convert piece to FEN character
   */
  private pieceToChar(piece: Piece): string {
    const chars: Record<string, string> = {
      pawn: 'p',
      knight: 'n',
      bishop: 'b',
      rook: 'r',
      queen: 'q',
      king: 'k',
    };

    const char = chars[piece.type];
    return piece.color === 'white' ? char.toUpperCase() : char;
  }

  /**
   * Client-side fallback validation (basic checks only)
   */
  private clientSideValidation(position: BoardPosition, move: Move): boolean {
    // Basic validation: check if piece exists and belongs to current player
    const piece = position.squares[move.from.rank][move.from.file];

    if (!piece) return false;
    if (piece.color !== position.turn) return false;

    // More sophisticated validation would happen on the backend
    return true;
  }

  /**
   * Analyze position using Stockfish engine
   */
  async analyzePosition(
    position: BoardPosition,
    depth: number = 15,
    multipv: number = 3,
    engine?: string
  ): Promise<EngineAnalysisResult> {
    try {
      const response = await fetch(`${this.baseURL}/api/engine/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          fen: this.positionToFEN(position),
          depth: depth,
          multipv: multipv,
          engine: engine,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return {
        lines: data.lines || [],
        depth: depth,
        spotId: data.spot_id || undefined,
        source: data.source || undefined,
      };
    } catch (error) {
      console.error('Failed to analyze position:', error);
      throw error;
    }
  }

  /**
   * Get engine health and spot metrics
   */
  async getEngineHealth(): Promise<EngineHealthInfo> {
    try {
      const response = await fetch(`${this.baseURL}/api/engine/health`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Failed to get engine health:', error);
      throw error;
    }
  }

  async predictImitator(
    position: BoardPosition,
    player: string,
    depth: number = 12,
    multipv: number = 8,
    topN: number = 3
  ): Promise<ImitatorResponse> {
    const response = await fetch(`${this.baseURL}/api/imitator/predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        fen: this.positionToFEN(position),
        player,
        depth,
        multipv,
        top_n: topN,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  }

  async getImitatorProfiles(): Promise<string[]> {
    const response = await fetch(`${this.baseURL}/api/imitator/profiles`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    return data.profiles || [];
  }
}

/**
 * Engine analysis types
 */
export interface EngineLine {
  multipv: number;
  score: number | string;
  pv: string[];
}

export interface EngineAnalysisResult {
  lines: EngineLine[];
  depth: number;
  spotId?: string;
  source?: string;
}

export interface EngineSpotMetrics {
  id: string;
  url: string;
  region: string;
  priority: number;
  enabled: boolean;
  status: string;
  avg_latency_ms: number;
  success_rate: number;
  total_requests: number;
  failure_count: number;
}

export interface EngineHealthInfo {
  status: string;
  engine_type: string;
  spots?: EngineSpotMetrics[];
}

export interface ImitatorMove {
  move: string;
  engine_eval: number | string;
  similarity: number;
  probability: number;
}

export interface ImitatorResponse {
  player: string;
  moves: ImitatorMove[];
}

// Global API instance
export const chessAPI = new ChessAPI();
