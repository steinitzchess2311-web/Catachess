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

export type SortOrder    = 'elo_desc' | 'year_desc' | 'year_asc';
export type ColorFilter  = 'any' | 'white' | 'black';
/** Player-perspective result: did THIS player win / lose / draw? */
export type PlayerResult = 'win' | 'loss' | 'draw';
/** Color-perspective score: which side won on the board? */
export type ColorResult  = 'white' | 'black' | 'draw';

export interface SearchFilters {
  color:        ColorFilter;
  playerResult: PlayerResult | '';   // player_result= (AND with colorResult)
  colorResult:  ColorResult  | '';   // result=        (AND with playerResult)
  yearFrom:     string;
  yearTo:       string;
  sort:         SortOrder;
}

export const DEFAULT_FILTERS: SearchFilters = {
  color:        'any',
  playerResult: '',
  colorResult:  '',
  yearFrom:     '',
  yearTo:       '',
  sort:         'elo_desc',
};
