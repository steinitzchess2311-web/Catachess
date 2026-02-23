// ============================================================
// useGameHistory — 历史对局列表，游标分页
// ============================================================

import { useCallback, useEffect, useRef, useState } from 'react';
import { listGames } from '../api';
import type { GameHistoryItem } from '../types';

export interface UseGameHistoryReturn {
  games: GameHistoryItem[];
  isLoading: boolean;
  hasMore: boolean;
  error: string | null;
  loadMore: () => void;
  refresh: () => void;
}

export function useGameHistory(userId: string): UseGameHistoryReturn {
  const [games, setGames] = useState<GameHistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 游标用 ref 存，不触发 re-render
  const cursorRef = useRef<string | undefined>(undefined);
  const loadingRef = useRef(false); // 防止并发请求

  const fetchPage = useCallback(
    async (reset: boolean) => {
      if (loadingRef.current) return;
      if (!reset && !hasMore) return;

      loadingRef.current = true;
      setIsLoading(true);
      setError(null);

      try {
        const cursor = reset ? undefined : cursorRef.current;
        const data = await listGames(userId, 20, cursor);

        setGames((prev) => (reset ? data.games : [...prev, ...data.games]));
        cursorRef.current = data.next_cursor ?? undefined;
        setHasMore(data.has_more);
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load games');
      } finally {
        setIsLoading(false);
        loadingRef.current = false;
      }
    },
    [userId, hasMore],
  );

  // 初始加载
  useEffect(() => {
    cursorRef.current = undefined;
    setGames([]);
    setHasMore(true);
    fetchPage(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId]);

  const loadMore = useCallback(() => fetchPage(false), [fetchPage]);
  const refresh = useCallback(() => fetchPage(true), [fetchPage]);

  return { games, isLoading, hasMore, error, loadMore, refresh };
}
