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

// ---- Filter types ----------------------------------------

export interface MastersFilters {
  since?: number; // year e.g. 2020
  until?: number;
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
