import { useState, useEffect, useRef, useCallback } from 'react';
import { fetchMasters } from './api';
import type { ExplorerResponse, MastersFilters } from './types';

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

export function useExplorer(fen: string): UseExplorerResult {
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

  const cacheKey = `masters:${fen}:${JSON.stringify(mastersFilters)}`;

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

      fetchMasters(fen, mastersFilters, controller.signal)
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
