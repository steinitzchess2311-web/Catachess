// ============================================================
// Explorer — Shared Types
// Base URL: https://database.catachess.com
// ============================================================

export type ExplorerTab = 'masters' | 'lichess' | 'player';

// ---- Speed / Rating enums --------------------------------

export type SpeedType =
  | 'ultraBullet'
  | 'bullet'
  | 'blitz'
  | 'rapid'
  | 'classical'
  | 'correspondence';

export const SPEED_LABELS: Record<SpeedType, string> = {
  ultraBullet: 'UltraBullet',
  bullet: 'Bullet',
  blitz: 'Blitz',
  rapid: 'Rapid',
  classical: 'Classical',
  correspondence: 'Corr.',
};

export const RATING_VALUES = [0, 1000, 1200, 1400, 1600, 1800, 2000, 2200, 2500] as const;
export type RatingValue = (typeof RATING_VALUES)[number];

// ---- API response types ----------------------------------

export interface GamePlayer {
  name: string;
  rating: number | null;
}

export interface GameRef {
  id: string;
  white: GamePlayer;
  black: GamePlayer;
  winner: 'white' | 'black' | null;
  year?: number | null;
  month?: string | null;
}

export interface MoveEntry {
  uci: string;
  san: string;
  white: number;
  draws: number;
  black: number;
  averageRating: number | null;
  game: GameRef | null;
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

/** Emitted on /player NDJSON stream before the final result is ready */
export interface QueueStatus {
  queuePosition: number;
}

// ---- Filter types ----------------------------------------

export interface MastersFilters {
  since?: number; // year e.g. 2020
  until?: number;
}

export interface LichessFilters {
  speeds: SpeedType[];
  ratings: RatingValue[];
  since?: string; // "YYYY-MM"
  until?: string;
}

export interface PlayerFilters {
  player: string;
  color: 'white' | 'black';
  speeds: SpeedType[];
  since?: string;
  until?: string;
}

export type PlayerLoadStatus = 'idle' | 'loading' | 'indexing' | 'ready' | 'error';

// ---- Type guards -----------------------------------------

export function isQueueStatus(obj: unknown): obj is QueueStatus {
  return (
    typeof obj === 'object' &&
    obj !== null &&
    'queuePosition' in obj &&
    !('moves' in obj)
  );
}

export function isExplorerResponse(obj: unknown): obj is ExplorerResponse {
  return typeof obj === 'object' && obj !== null && 'moves' in obj && Array.isArray((obj as ExplorerResponse).moves);
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
