import { useState, useEffect, useRef, useCallback } from 'react';
import { fetchMasters, fetchLichess, fetchPlayer } from './api';
import { isQueueStatus } from './types';
import type {
  ExplorerTab,
  ExplorerResponse,
  MastersFilters,
  LichessFilters,
  PlayerFilters,
  PlayerLoadStatus,
} from './types';

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
  queuePosition: number | null;
  playerStatus: PlayerLoadStatus;
  tab: ExplorerTab;
  setTab: (t: ExplorerTab) => void;
  mastersFilters: MastersFilters;
  setMastersFilters: (f: MastersFilters) => void;
  lichessFilters: LichessFilters;
  setLichessFilters: (f: LichessFilters) => void;
  playerFilters: PlayerFilters;
  setPlayerFilters: (f: PlayerFilters) => void;
  triggerPlayerFetch: () => void;
}

const DEFAULT_LICHESS: LichessFilters = { speeds: [], ratings: [] };
const DEFAULT_PLAYER: PlayerFilters  = { player: '', color: 'white', speeds: [] };
const DEFAULT_MASTERS: MastersFilters = {};

export function useExplorer(fen: string): UseExplorerResult {
  // ---- persisted filters -----------------------------------
  const [tab, setTab]                         = useStoredState<ExplorerTab>('explorer.tab', 'masters');
  const [mastersFilters, setMastersFilters]   = useStoredState<MastersFilters>('explorer.masters', DEFAULT_MASTERS);
  const [lichessFilters, setLichessFilters]   = useStoredState<LichessFilters>('explorer.lichess', DEFAULT_LICHESS);
  const [playerFilters,  setPlayerFilters]    = useStoredState<PlayerFilters>('explorer.player',  DEFAULT_PLAYER);

  // ---- fetch state -----------------------------------------
  const [data,         setData]         = useState<ExplorerResponse | null>(null);
  const [loading,      setLoading]      = useState(false);
  const [error,        setError]        = useState<string | null>(null);
  const [queuePosition, setQueuePosition] = useState<number | null>(null);
  const [playerStatus,  setPlayerStatus]  = useState<PlayerLoadStatus>('idle');

  // ---- refs ------------------------------------------------
  const cacheRef = useRef<Map<string, ExplorerResponse>>(new Map());
  const abortRef = useRef<AbortController | null>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // ---- cache key -------------------------------------------
  const filters  = tab === 'masters' ? mastersFilters : tab === 'lichess' ? lichessFilters : playerFilters;
  const cacheKey = `${tab}:${fen}:${JSON.stringify(filters)}`;

  // ---- core effect -----------------------------------------
  useEffect(() => {
    if (!fen) return;

    // cancel previous debounce + request
    if (timerRef.current !== null) { clearTimeout(timerRef.current); timerRef.current = null; }
    abortRef.current?.abort();
    abortRef.current = null;

    // player tab: manual trigger only
    if (tab === 'player') return;

    // cache hit — instant, no network
    const cached = cacheRef.current.get(cacheKey);
    if (cached) {
      setData(cached);
      setLoading(false);
      setError(null);
      return;
    }

    // No cache hit — clear stale data immediately so old moves can't be
    // re-clicked while the debounce timer is running (prevents the
    // "Nxd4 added ten times" bug when the user clicks quickly).
    setData(null);
    setError(null);

    // debounce network request
    timerRef.current = setTimeout(() => {
      timerRef.current = null;
      const controller = new AbortController();
      abortRef.current = controller;
      setLoading(true);
      setError(null);

      const done = (result: ExplorerResponse) => {
        cacheRef.current.set(cacheKey, result);
        setData(result);
        setLoading(false);
      };
      const fail = (e: unknown) => {
        if ((e as Error)?.name === 'AbortError') return;
        setError((e as Error)?.message ?? 'Unknown error');
        setLoading(false);
      };

      if (tab === 'masters') {
        // Single request — returns moves + topGames together
        fetchMasters(fen, mastersFilters, controller.signal).then(done).catch(fail);
      } else {
        fetchLichess(fen, lichessFilters, controller.signal).then(done).catch(fail);
      }
    }, 250);

    return () => {
      if (timerRef.current !== null) { clearTimeout(timerRef.current); timerRef.current = null; }
      abortRef.current?.abort();
      abortRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cacheKey]);

  // ---- player manual trigger --------------------------------
  const triggerPlayerFetch = useCallback(() => {
    if (!playerFilters.player.trim()) return;

    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    const cached = cacheRef.current.get(cacheKey);
    if (cached) {
      setData(cached);
      setPlayerStatus('ready');
      setLoading(false);
      return;
    }

    setData(null);
    setLoading(true);
    setQueuePosition(null);
    setPlayerStatus('loading');
    setError(null);

    (async () => {
      try {
        for await (const item of fetchPlayer(fen, playerFilters, controller.signal)) {
          if (controller.signal.aborted) break;
          if (isQueueStatus(item)) {
            setQueuePosition(item.queuePosition);
            setPlayerStatus('indexing');
          } else {
            setData(item);
            setQueuePosition(null);
            setPlayerStatus('ready');
            setLoading(false);
            cacheRef.current.set(cacheKey, item);
          }
        }
        setLoading(false);
      } catch (e) {
        if ((e as Error)?.name === 'AbortError') return;
        setError((e as Error)?.message ?? 'Unknown error');
        setPlayerStatus('error');
        setLoading(false);
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cacheKey, fen, playerFilters]);

  return {
    data, loading, error,
    queuePosition, playerStatus,
    tab, setTab,
    mastersFilters, setMastersFilters,
    lichessFilters, setLichessFilters,
    playerFilters,  setPlayerFilters,
    triggerPlayerFetch,
  };
}

export { useExplorer as default };
