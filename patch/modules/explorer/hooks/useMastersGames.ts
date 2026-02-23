// ============================================================
// useMastersGames — /masters/games cursor 分页 hook
// 支持多棋手 player[] 过滤
// ============================================================

import { useState, useEffect, useCallback, useRef } from 'react';
import { fetchMastersGames } from '../api';
import type { GameListItem, SortOrder } from '../types';

export interface UseMastersGamesResult {
  games: GameListItem[];
  loading: boolean;
  error: string | null;
  hasMore: boolean;
  loadMore: () => void;
  total: number;
}

export function useMastersGames(
  fen: string,
  players: string[],
  sort: SortOrder,
): UseMastersGamesResult {
  const [games, setGames] = useState<GameListItem[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);

  const keyRef = useRef('');
  const key = `${fen}||${JSON.stringify(players)}||${sort}`;

  // FEN / players / sort 变化时重置并首次加载
  useEffect(() => {
    if (!fen) return;

    keyRef.current = key;
    setGames([]);
    setCursor(null);
    setHasMore(false);
    setError(null);
    setTotal(0);
    setLoading(true);

    const controller = new AbortController();

    fetchMastersGames(fen, players, sort, null, controller.signal)
      .then(data => {
        if (keyRef.current !== key) return;
        setGames(data.games);
        setCursor(data.next_cursor);
        setHasMore(data.next_cursor !== null);
        setTotal(data.games.length);
        setLoading(false);
      })
      .catch((err: unknown) => {
        if ((err as Error)?.name === 'AbortError') return;
        if (keyRef.current !== key) return;
        setError((err as Error)?.message ?? 'Request failed');
        setLoading(false);
      });

    return () => controller.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);

  const loadMore = useCallback(() => {
    if (loading || !hasMore || !cursor || !fen) return;

    const currentKey = key;
    setLoading(true);

    fetchMastersGames(fen, players, sort, cursor)
      .then(data => {
        if (keyRef.current !== currentKey) return;
        setGames(prev => {
          const next = [...prev, ...data.games];
          setTotal(next.length);
          return next;
        });
        setCursor(data.next_cursor);
        setHasMore(data.next_cursor !== null);
        setLoading(false);
      })
      .catch((err: unknown) => {
        if ((err as Error)?.name === 'AbortError') return;
        if (keyRef.current !== currentKey) return;
        setError((err as Error)?.message ?? 'Request failed');
        setLoading(false);
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fen, players, sort, cursor, loading, hasMore, key]);

  return { games, loading, error, hasMore, loadMore, total };
}
