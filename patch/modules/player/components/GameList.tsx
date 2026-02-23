// ============================================================
// GameList — 对局列表 + IntersectionObserver 无限滚动
// ============================================================

import React, { useCallback, useRef } from 'react';
import { GameCard } from './GameCard';
import type { GameListItem } from '../types';

interface Props {
  games: GameListItem[];
  loading: boolean;
  error: string | null;
  hasMore: boolean;
  total: number;
  onLoadMore: () => void;
}

function SkeletonCard() {
  return (
    <div className="ps-card ps-card--skeleton" aria-hidden>
      <div className="ps-card__accent" />
      <div className="ps-card__players">
        <div className="ps-card__player">
          <div className="ps-skel ps-skel--name" />
          <div className="ps-skel ps-skel--elo" />
        </div>
        <div className="ps-card__player">
          <div className="ps-skel ps-skel--name" />
          <div className="ps-skel ps-skel--elo" />
        </div>
      </div>
      <div className="ps-card__result">
        <div className="ps-skel ps-skel--result" />
      </div>
      <div className="ps-card__meta">
        <div className="ps-skel ps-skel--meta" />
      </div>
    </div>
  );
}

export function GameList({ games, loading, error, hasMore, total, onLoadMore }: Props) {
  // IntersectionObserver 触发加载更多
  const observerRef = useRef<IntersectionObserver | null>(null);
  const sentinelRef = useCallback(
    (node: HTMLDivElement | null) => {
      if (observerRef.current) observerRef.current.disconnect();
      if (!node) return;
      observerRef.current = new IntersectionObserver(
        (entries) => {
          if (entries[0]?.isIntersecting) onLoadMore();
        },
        { rootMargin: '200px' },
      );
      observerRef.current.observe(node);
    },
    [onLoadMore],
  );

  if (error) {
    return (
      <div className="ps-status ps-status--error">
        <span>⚠</span> {error}
      </div>
    );
  }

  if (!loading && games.length === 0) return null;

  return (
    <div className="ps-list">
      {games.map((g, i) => (
        <GameCard
          key={g.id}
          game={g}
          delay={Math.min(i, 12) * 30}
        />
      ))}

      {/* 首次加载骨架屏 */}
      {loading && games.length === 0 && (
        <>
          {Array.from({ length: 6 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </>
      )}

      {/* 加载更多的触发点 */}
      {hasMore && !loading && <div ref={sentinelRef} className="ps-sentinel" aria-hidden />}

      {/* 加载更多时的 loading 提示 */}
      {loading && games.length > 0 && (
        <div className="ps-status ps-status--loading">
          <span className="ps-dot" /><span className="ps-dot" /><span className="ps-dot" />
        </div>
      )}

      {/* 到底了 */}
      {!hasMore && !loading && games.length > 0 && (
        <div className="ps-status ps-status--end">
          {total} games total
        </div>
      )}
    </div>
  );
}
