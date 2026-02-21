import type { ExplorerResponse, MastersFilters, GameDetail } from './types';

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
  signal?: AbortSignal,
  options?: FetchMastersOptions,
): Promise<ExplorerResponse> {
  const url = new URL(`${BASE}/masters`);
  url.searchParams.set('fen', fen);
  if (filters.since != null) url.searchParams.set('since', String(filters.since));
  if (filters.until != null) url.searchParams.set('until', String(filters.until));
  if (options?.movesCount != null) url.searchParams.set('moves', String(options.movesCount));
  if (options?.topGames != null) url.searchParams.set('topGames', String(options.topGames));

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
