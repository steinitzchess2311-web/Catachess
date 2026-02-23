// ============================================================
// Hook: 棋手对局无限滚动（cursor 分页）
// ============================================================

import { useState, useEffect, useCallback, useRef } from 'react';
import { fetchSearchGames } from '../api';
import type { GameListItem, SearchFilters } from '../types';

export interface UsePlayerGamesResult {
  games: GameListItem[];
  loading: boolean;
  error: string | null;
  hasMore: boolean;
  loadMore: () => void;
  total: number;
}

export function usePlayerGames(
  player: string,
  filters: SearchFilters,
): UsePlayerGamesResult {
  const [games, setGames] = useState<GameListItem[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);

  // 用于标记是否是首次加载（player 或 filters 变化时重置）
  const keyRef = useRef('');

  const key = `${player}||${JSON.stringify(filters)}`;

  useEffect(() => {
    if (!player.trim()) {
      setGames([]);
      setCursor(null);
      setHasMore(false);
      setError(null);
      setTotal(0);
      return;
    }

    keyRef.current = key;

    setGames([]);
    setCursor(null);
    setHasMore(false);
    setError(null);
    setTotal(0);
    setLoading(true);

    const controller = new AbortController();

    fetchSearchGames(player, filters, null, controller.signal)
      .then((data) => {
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
        setError((err as Error)?.message ?? '请求失败');
        setLoading(false);
      });

    return () => controller.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);

  const loadMore = useCallback(() => {
    if (loading || !hasMore || !cursor || !player.trim()) return;

    const currentKey = key;
    setLoading(true);

    fetchSearchGames(player, filters, cursor)
      .then((data) => {
        if (keyRef.current !== currentKey) return;
        setGames((prev) => {
          const newGames = [...prev, ...data.games];
          setTotal(newGames.length);
          return newGames;
        });
        setCursor(data.next_cursor);
        setHasMore(data.next_cursor !== null);
        setLoading(false);
      })
      .catch((err: unknown) => {
        if ((err as Error)?.name === 'AbortError') return;
        if (keyRef.current !== currentKey) return;
        setError((err as Error)?.message ?? '请求失败');
        setLoading(false);
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [player, filters, cursor, loading, hasMore, key]);

  return { games, loading, error, hasMore, loadMore, total };
}
