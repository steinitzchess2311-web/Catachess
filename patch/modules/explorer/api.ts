import type {
  ExplorerResponse,
  MastersFilters,
  LichessFilters,
  PlayerFilters,
  QueueStatus,
} from './types';
import { isQueueStatus, isExplorerResponse } from './types';

const BASE = 'https://database.catachess.com';

// ---- Masters -----------------------------------------------

export interface FetchMastersOptions {
  /** Max candidate moves to return. Pass 0 to skip moves (games-only request). Default: 12 */
  movesCount?: number;
  /** Max top games to return. Pass 0 to skip games (moves-only request). Default: 15 */
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

// ---- Lichess -----------------------------------------------

export async function fetchLichess(
  fen: string,
  filters: LichessFilters,
  signal?: AbortSignal,
): Promise<ExplorerResponse> {
  const url = new URL(`${BASE}/lichess`);
  url.searchParams.set('fen', fen);
  if (filters.speeds.length) url.searchParams.set('speeds', filters.speeds.join(','));
  if (filters.ratings.length) url.searchParams.set('ratings', filters.ratings.map(String).join(','));
  if (filters.since) url.searchParams.set('since', filters.since);
  if (filters.until) url.searchParams.set('until', filters.until);

  const res = await fetch(url.toString(), { signal });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail ?? `HTTP ${res.status}`);
  }
  return res.json();
}

// ---- Player (NDJSON stream) ---------------------------------

/**
 * Async generator for the /player endpoint.
 *
 * Yields:
 *   - ExplorerResponse — immediate result (may be empty on first emit)
 *   - QueueStatus      — indexing in progress, shows queue position
 *   - ExplorerResponse — final result after indexing completes
 *
 * If the player is cached server-side (< 3 h), only one ExplorerResponse
 * is emitted and the generator completes immediately.
 */
export async function* fetchPlayer(
  fen: string,
  filters: PlayerFilters,
  signal?: AbortSignal,
): AsyncGenerator<ExplorerResponse | QueueStatus> {
  const url = new URL(`${BASE}/player`);
  url.searchParams.set('player', filters.player);
  url.searchParams.set('color', filters.color);
  url.searchParams.set('fen', fen);
  if (filters.speeds.length) url.searchParams.set('speeds', filters.speeds.join(','));
  if (filters.since) url.searchParams.set('since', filters.since);
  if (filters.until) url.searchParams.set('until', filters.until);

  const res = await fetch(url.toString(), { signal });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail ?? `HTTP ${res.status}`);
  }

  const reader = res.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() ?? ''; // hold incomplete trailing line

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed) continue;
        try {
          const parsed: unknown = JSON.parse(trimmed);
          if (isQueueStatus(parsed) || isExplorerResponse(parsed)) {
            yield parsed;
          }
        } catch {
          // skip malformed line
        }
      }
    }

    // flush any remainder
    const trimmed = buffer.trim();
    if (trimmed) {
      try {
        const parsed: unknown = JSON.parse(trimmed);
        if (isQueueStatus(parsed) || isExplorerResponse(parsed)) {
          yield parsed;
        }
      } catch {
        // ignore
      }
    }
  } finally {
    reader.cancel();
  }
}
