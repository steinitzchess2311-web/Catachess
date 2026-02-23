import type { ExplorerResponse, MastersFilters, GameDetail, GamesListResponse, SortOrder } from './types';

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
  signal?: AbortSignal,
  options?: FetchMastersOptions,
): Promise<ExplorerResponse> {
  const url = new URL(`${BASE}/masters`);
  url.searchParams.set('fen', fen);
  // player= filter (when present, backend ignores since/until)
  players.forEach(p => url.searchParams.append('player', p));
  // year filters — only sent when no player filter (backend ignores them otherwise)
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
  sort: SortOrder,
  cursor: string | null,
  signal?: AbortSignal,
): Promise<GamesListResponse> {
  const url = new URL(`${BASE}/masters/games`);
  url.searchParams.set('fen', fen);
  url.searchParams.set('sort', sort);
  players.forEach(p => url.searchParams.append('player', p));
  if (cursor) url.searchParams.set('cursor', cursor);

  const res = await fetch(url.toString(), { signal });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail ?? `HTTP ${res.status}`);
  }
  return res.json();
}

export interface PlayerStatsResponse {
  wins: number;
  draws: number;
  losses: number;
  total: number;
}

/** /masters/stats — win/draw/loss counts from the player's perspective */
export async function fetchMastersStats(
  fen: string,
  players: string[],
  signal?: AbortSignal,
): Promise<PlayerStatsResponse> {
  const url = new URL(`${BASE}/masters/stats`);
  url.searchParams.set('fen', fen);
  players.forEach(p => url.searchParams.append('player', p));

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
