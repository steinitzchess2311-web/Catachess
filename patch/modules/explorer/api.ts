import type { ExplorerResponse, MastersFilters, GameDetail, GamesListResponse, SortOrder, PlayerColorFilter } from './types';

const BASE = 'https://database.catachess.com';

export interface FetchMastersOptions {
  /** Max candidate moves to return. Default: 12 */
  movesCount?: number;
  /** Max top games to return. Default: 15 */
  topGames?: number;
}

export async function fetchMasters(
  fen: string,
  filters: MastersFilters,
  players: string[] = [],
  playerColor: PlayerColorFilter = 'any',
  signal?: AbortSignal,
  options?: FetchMastersOptions,
): Promise<ExplorerResponse> {
  const url = new URL(`${BASE}/masters`);
  url.searchParams.set('fen', fen);
  players.forEach(p => url.searchParams.append('player', p));
  if (players.length > 0 && playerColor !== 'any') {
    url.searchParams.set('player_color', playerColor);
  }
  if (players.length === 0) {
    if (filters.since != null) url.searchParams.set('since', String(filters.since));
    if (filters.until != null) url.searchParams.set('until', String(filters.until));
  }
  if (options?.movesCount != null) url.searchParams.set('moves', String(options.movesCount));
  if (options?.topGames != null) url.searchParams.set('topGames', String(options.topGames));

  const res = await fetch(url.toString(), { signal });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail ?? `HTTP ${res.status}`);
  }
  return res.json();
}

/** /masters/games — 局面内对局列表，支持多棋手过滤 + cursor 分页 */
export async function fetchMastersGames(
  fen: string,
  players: string[],
  playerColor: PlayerColorFilter,
  sort: SortOrder,
  cursor: string | null,
  signal?: AbortSignal,
): Promise<GamesListResponse> {
  const url = new URL(`${BASE}/masters/games`);
  url.searchParams.set('fen', fen);
  url.searchParams.set('sort', sort);
  players.forEach(p => url.searchParams.append('player', p));
  if (players.length > 0 && playerColor !== 'any') {
    url.searchParams.set('player_color', playerColor);
  }
  if (cursor) url.searchParams.set('cursor', cursor);

  const res = await fetch(url.toString(), { signal });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail ?? `HTTP ${res.status}`);
  }
  return res.json();
}

export interface PlayerSuggestion {
  name: string;
  games: number;
}

/** /search/players — player name prefix autocomplete */
export async function fetchPlayerSuggestions(
  q: string,
  limit = 8,
  signal?: AbortSignal,
): Promise<{ players: PlayerSuggestion[] }> {
  const url = new URL(`${BASE}/search/players`);
  url.searchParams.set('q', q);
  url.searchParams.set('limit', String(limit));
  const res = await fetch(url.toString(), { signal });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail ?? `HTTP ${res.status}`);
  }
  return res.json();
}

export async function fetchGame(id: string, signal?: AbortSignal): Promise<GameDetail> {
  const res = await fetch(`${BASE}/game/${id}`, { signal });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail ?? `HTTP ${res.status}`);
  }
  return res.json();
}
