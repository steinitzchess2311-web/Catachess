import { useState, useEffect, useRef, useCallback } from 'react';
import { fetchMasters, fetchLichess, fetchPlayer } from './api';
import { isQueueStatus } from './types';
import type {
  ExplorerTab,
  ExplorerResponse,
  GameRef,
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
        // storage unavailable — continue without persistence
      }
      setVal(v);
    },
    [key],
  );

  return [val, set];
}

// ---- Public hook -------------------------------------------

export interface UseExplorerResult {
  // moves data (Phase 1)
  data: ExplorerResponse | null;
  loading: boolean;
  error: string | null;

  // top games data (Phase 2 — Masters only, parallel fetch)
  topGames: GameRef[] | null;
  topGamesLoading: boolean;

  // player state
  queuePosition: number | null;
  playerStatus: PlayerLoadStatus;

  // tab
  tab: ExplorerTab;
  setTab: (t: ExplorerTab) => void;

  // per-tab filters
  mastersFilters: MastersFilters;
  setMastersFilters: (f: MastersFilters) => void;
  lichessFilters: LichessFilters;
  setLichessFilters: (f: LichessFilters) => void;
  playerFilters: PlayerFilters;
  setPlayerFilters: (f: PlayerFilters) => void;

  /** Manually trigger a /player fetch. No-op if player field is empty. */
  triggerPlayerFetch: () => void;
}

const DEFAULT_LICHESS: LichessFilters = { speeds: [], ratings: [] };
const DEFAULT_PLAYER: PlayerFilters = { player: '', color: 'white', speeds: [] };
const DEFAULT_MASTERS: MastersFilters = {};

export function useExplorer(fen: string): UseExplorerResult {
  // ---- persisted filter state ----------------------------------
  const [tab, setTab] = useStoredState<ExplorerTab>('explorer.tab', 'masters');
  const [mastersFilters, setMastersFilters] = useStoredState<MastersFilters>(
    'explorer.masters',
    DEFAULT_MASTERS,
  );
  const [lichessFilters, setLichessFilters] = useStoredState<LichessFilters>(
    'explorer.lichess',
    DEFAULT_LICHESS,
  );
  const [playerFilters, setPlayerFilters] = useStoredState<PlayerFilters>(
    'explorer.player',
    DEFAULT_PLAYER,
  );

  // ---- Phase 1: moves data ------------------------------------
  const [data, setData] = useState<ExplorerResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // ---- Phase 2: top games (Masters only) ----------------------
  const [topGames, setTopGames] = useState<GameRef[] | null>(null);
  const [topGamesLoading, setTopGamesLoading] = useState(false);

  // ---- Player state -------------------------------------------
  const [queuePosition, setQueuePosition] = useState<number | null>(null);
  const [playerStatus, setPlayerStatus] = useState<PlayerLoadStatus>('idle');

  // ---- Refs ---------------------------------------------------
  // Phase 1
  const cacheRef  = useRef<Map<string, ExplorerResponse>>(new Map());
  const abortRef  = useRef<AbortController | null>(null);
  const timerRef  = useRef<ReturnType<typeof setTimeout> | null>(null);
  // Phase 2 (games)
  const gamesCacheRef = useRef<Map<string, GameRef[]>>(new Map());
  const gamesAbortRef = useRef<AbortController | null>(null);

  // ---- Cache keys ---------------------------------------------
  const filters =
    tab === 'masters' ? mastersFilters : tab === 'lichess' ? lichessFilters : playerFilters;
  const cacheKey      = `${tab}:${fen}:${JSON.stringify(filters)}`;
  const gamesCacheKey = `games:masters:${fen}:${JSON.stringify(mastersFilters)}`;

  // ---- Core effect --------------------------------------------
  useEffect(() => {
    if (!fen) return;

    // Cancel pending debounce + in-flight requests
    if (timerRef.current !== null) { clearTimeout(timerRef.current); timerRef.current = null; }
    abortRef.current?.abort();    abortRef.current = null;
    gamesAbortRef.current?.abort(); gamesAbortRef.current = null;

    // Reset games when position changes (non-Masters tabs don't use them)
    if (tab !== 'masters') {
      setTopGames(null);
      setTopGamesLoading(false);
    }

    // Player: manual-trigger only
    if (tab === 'player') return;

    // Phase 1 cache hit
    const cached = cacheRef.current.get(cacheKey);
    if (cached) {
      setData(cached);
      setLoading(false);
      setError(null);
    }

    // Phase 2 cache hit (Masters only)
    if (tab === 'masters') {
      const cachedGames = gamesCacheRef.current.get(gamesCacheKey);
      if (cachedGames) {
        setTopGames(cachedGames);
        setTopGamesLoading(false);
      }
      // If both are cached, we're done
      if (cached && cachedGames) return;
    } else if (cached) {
      return;
    }

    // Debounce before firing network requests
    timerRef.current = setTimeout(() => {
      timerRef.current = null;

      const fail = (e: unknown) => {
        if ((e as Error)?.name === 'AbortError') return;
        setError((e as Error)?.message ?? 'Unknown error');
        setLoading(false);
      };

      if (tab === 'masters') {
        // ---- Phase 1: moves only (topGames=0) ---------------
        if (!cached) {
          const ctrl1 = new AbortController();
          abortRef.current = ctrl1;
          setLoading(true);
          setError(null);

          fetchMasters(fen, mastersFilters, ctrl1.signal, { topGames: 0 })
            .then((result) => {
              cacheRef.current.set(cacheKey, result);
              setData(result);
              setLoading(false);
            })
            .catch(fail);
        }

        // ---- Phase 2: games only (moves=0), parallel --------
        const cachedGames = gamesCacheRef.current.get(gamesCacheKey);
        if (!cachedGames) {
          const ctrl2 = new AbortController();
          gamesAbortRef.current = ctrl2;
          setTopGamesLoading(true);

          fetchMasters(fen, mastersFilters, ctrl2.signal, { movesCount: 0, topGames: 15 })
            .then((result) => {
              gamesCacheRef.current.set(gamesCacheKey, result.topGames);
              setTopGames(result.topGames);
              setTopGamesLoading(false);
            })
            .catch((e) => {
              if ((e as Error)?.name !== 'AbortError') setTopGamesLoading(false);
            });
        }
      } else {
        // ---- Lichess: single request -------------------------
        const ctrl = new AbortController();
        abortRef.current = ctrl;
        setLoading(true);
        setError(null);

        fetchLichess(fen, lichessFilters, ctrl.signal)
          .then((result) => {
            cacheRef.current.set(cacheKey, result);
            setData(result);
            setLoading(false);
          })
          .catch(fail);
      }
    }, 250);

    return () => {
      if (timerRef.current !== null) { clearTimeout(timerRef.current); timerRef.current = null; }
      abortRef.current?.abort();    abortRef.current = null;
      gamesAbortRef.current?.abort(); gamesAbortRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cacheKey, gamesCacheKey]);

  // ---- Player manual trigger ----------------------------------
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
    data,
    loading,
    error,
    topGames,
    topGamesLoading,
    queuePosition,
    playerStatus,
    tab,
    setTab,
    mastersFilters,
    setMastersFilters,
    lichessFilters,
    setLichessFilters,
    playerFilters,
    setPlayerFilters,
    triggerPlayerFetch,
  };
}

export { useExplorer as default };
