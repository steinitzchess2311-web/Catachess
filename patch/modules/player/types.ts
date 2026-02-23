// ============================================================
// Player Search — 共享类型
// Base URL: https://database.catachess.com
// ============================================================

export interface PlayerSuggestion {
  name: string;
  games: number;
}

export interface PlayerSuggestionsResponse {
  players: PlayerSuggestion[];
}

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

export type SortOrder = 'elo_desc' | 'year_desc' | 'year_asc';
export type ColorFilter = 'any' | 'white' | 'black';
export type ResultFilter = 'white' | 'black' | 'draw';

export interface SearchFilters {
  color: ColorFilter;
  result: ResultFilter | '';
  yearFrom: string;
  yearTo: string;
  sort: SortOrder;
}

export const DEFAULT_FILTERS: SearchFilters = {
  color: 'any',
  result: '',
  yearFrom: '',
  yearTo: '',
  sort: 'elo_desc',
};
