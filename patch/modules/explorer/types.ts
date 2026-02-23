// ============================================================
// Explorer — Shared Types
// Base URL: https://database.catachess.com
// ============================================================

// ---- API response types ----------------------------------

export interface GamePlayer {
  name: string;
  rating: number | null;
}

export interface GameRef {
  id: string;
  uci?: string;            // present in topGames entries from the API
  white: GamePlayer;
  black: GamePlayer;
  winner: 'white' | 'black' | null;
  year?: number | null;
  month?: string | null;   // "YYYY-MM"
}

export interface MoveEntry {
  uci: string;
  san: string;
  white: number;
  draws: number;
  black: number;
  averageRating: number | null;
  game: GameRef | null;
  opening?: { eco: string; name: string } | null;
}

export interface ExplorerResponse {
  white: number;
  draws: number;
  black: number;
  moves: MoveEntry[];
  topGames: GameRef[];
  recentGames: GameRef[];
  opening: null;
}

export interface GameDetail extends GameRef {
  event: string | null;
  moves: string | null; // space-separated UCI, e.g. "e2e4 e7e5 g1f3"
}

// ---- Filter types ----------------------------------------

export interface MastersFilters {
  since?: number; // year e.g. 2020
  until?: number;
}

// ---- /masters/games response types ---------------------------

export type SortOrder = 'elo_desc' | 'year_desc' | 'year_asc';

export interface GameListItem {
  id: string;
  white: string;
  black: string;
  white_elo: number | null;
  black_elo: number | null;
  avg_elo: number | null;
  result: 'white' | 'black' | 'draw';
  year: number | null;
  event: string | null;
}

export interface GamesListResponse {
  games: GameListItem[];
  next_cursor: string | null;
}

// ---- Utility ---------------------------------------------

export function totalGames(data: { white: number; draws: number; black: number }): number {
  return data.white + data.draws + data.black;
}

export function winRates(data: { white: number; draws: number; black: number }) {
  const total = totalGames(data);
  if (total === 0) return { white: 0, draw: 0, black: 0 };
  return {
    white: (data.white / total) * 100,
    draw: (data.draws / total) * 100,
    black: (data.black / total) * 100,
  };
}

export function formatGames(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(n >= 10_000 ? 0 : 1)}k`;
  return String(n);
}
