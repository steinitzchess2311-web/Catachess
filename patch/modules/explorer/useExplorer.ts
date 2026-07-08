import { useState, useEffect, useRef, useCallback } from 'react';
import { fetchMasters } from './api';
import type { ExplorerResponse, MastersFilters, PlayerColorFilter } from './types';

// ---- Stored state ------------------------------------------

function useStoredState<T>(key: string, defaultValue: T): [T, (v: T) => void] {
  const [val, setVal] = useState<T>(() => {
    try {
      const stored = localStorage.getItem(key);
      return stored !== null ? (JSON.parse(stored) as T) : defaultValue;
    } catch {
      return defaultValue;
    }
  });

  const set = useCallback(
    (v: T) => {
      try {
        localStorage.setItem(key, JSON.stringify(v));
      } catch {
        // storage unavailable
      }
      setVal(v);
    },
    [key],
  );

  return [val, set];
}

// ---- Public interface --------------------------------------

export interface UseExplorerResult {
  data: ExplorerResponse | null;
  loading: boolean;
  error: string | null;
  mastersFilters: MastersFilters;
  setMastersFilters: (f: MastersFilters) => void;
}

const DEFAULT_MASTERS: MastersFilters = {};

/**
 * Fetches /masters for move stats + aggregate counts.
 * When `players` is non-empty, all stats are scoped to those players.
 * Year filters (since/until) are skipped when players are active.
 */
export function useExplorer(
  fen: string,
  players: string[] = [],
  playerColor: PlayerColorFilter = 'any',
): UseExplorerResult {
  const [mastersFilters, setMastersFilters] = useStoredState<MastersFilters>(
    'explorer.masters',
    DEFAULT_MASTERS,
  );

  const [data,    setData]    = useState<ExplorerResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState<string | null>(null);

  const cacheRef = useRef<Map<string, ExplorerResponse>>(new Map());
  const abortRef = useRef<AbortController | null>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Cache key: fen + year filters (only relevant when no player filter) + players
  const playersKey = players.join('\0');
  const filtersKey = players.length === 0 ? JSON.stringify(mastersFilters) : '{}';
  const cacheKey   = `masters:${fen}:${filtersKey}:${playersKey}:${playerColor}`;

  useEffect(() => {
    if (!fen) return;

    if (timerRef.current !== null) { clearTimeout(timerRef.current); timerRef.current = null; }
    abortRef.current?.abort();
    abortRef.current = null;

    const cached = cacheRef.current.get(cacheKey);
    if (cached) {
      setData(cached);
      setLoading(false);
      setError(null);
      return;
    }

    setData(null);
    setError(null);

    timerRef.current = setTimeout(() => {
      timerRef.current = null;
      const controller = new AbortController();
      abortRef.current = controller;
      setLoading(true);
      setError(null);

      fetchMasters(fen, mastersFilters, players, playerColor, controller.signal)
        .then((result) => {
          cacheRef.current.set(cacheKey, result);
          setData(result);
          setLoading(false);
        })
        .catch((e: unknown) => {
          if ((e as Error)?.name === 'AbortError') return;
          setError((e as Error)?.message ?? 'Unknown error');
          setLoading(false);
        });
    }, 250);

    return () => {
      if (timerRef.current !== null) { clearTimeout(timerRef.current); timerRef.current = null; }
      abortRef.current?.abort();
      abortRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cacheKey]);

  return { data, loading, error, mastersFilters, setMastersFilters };
}

export { useExplorer as default };
