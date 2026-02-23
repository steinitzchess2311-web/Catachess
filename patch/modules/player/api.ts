// ============================================================
// Player Search — API 客户端
// ============================================================

import type {
  PlayerSuggestionsResponse,
  GamesListResponse,
  SearchFilters,
} from './types';

const BASE = 'https://database.catachess.com';

/** /search/players — 棋手名字前缀自动补全 */
export async function fetchPlayerSuggestions(
  q: string,
  limit = 8,
  signal?: AbortSignal,
): Promise<PlayerSuggestionsResponse> {
  const url = new URL(`${BASE}/search/players`);
  url.searchParams.set('q', q);
  url.searchParams.set('limit', String(limit));

  const res = await fetch(url.toString(), { signal });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

/** /search/games — 棋手全局对局搜索 */
export async function fetchSearchGames(
  player: string,
  filters: SearchFilters,
  cursor: string | null,
  signal?: AbortSignal,
): Promise<GamesListResponse> {
  const url = new URL(`${BASE}/search/games`);
  url.searchParams.set('player', player);

  if (filters.color && filters.color !== 'any') {
    url.searchParams.set('color', filters.color);
  }
  if (filters.result) {
    url.searchParams.set('result', filters.result);
  }
  if (filters.yearFrom) {
    url.searchParams.set('year_from', filters.yearFrom);
  }
  if (filters.yearTo) {
    url.searchParams.set('year_to', filters.yearTo);
  }
  if (filters.sort) {
    url.searchParams.set('sort', filters.sort);
  }
  if (cursor) {
    url.searchParams.set('cursor', cursor);
  }

  const res = await fetch(url.toString(), { signal });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}
