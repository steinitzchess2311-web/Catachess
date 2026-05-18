// ============================================================
// HistoryList — 历史对局列表
// 风格对标 player 模块的 GameCard，支持无限滚动
// ============================================================

import React, { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import type { GameHistoryItem } from '../types';

// 结果文本映射
function resultLabel(item: GameHistoryItem): string {
  if (!item.result) return '—';
  if (item.result === '1-0') return item.your_color === 'white' ? 'Win' : 'Loss';
  if (item.result === '0-1') return item.your_color === 'black' ? 'Win' : 'Loss';
  return 'Draw';
}

function resultClass(item: GameHistoryItem): string {
  const label = resultLabel(item);
  if (label === 'Win') return 'ug-hist-card--win';
  if (label === 'Loss') return 'ug-hist-card--loss';
  return 'ug-hist-card--draw';
}

/** 格式化时间控制为 "5+3" */
function formatTC(tc: GameHistoryItem['time_control']): string {
  return `${tc.initial / 60}+${tc.increment}`;
}

/** 格式化日期 */
function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

// ---- 单条卡片 ------------------------------------------------

interface HistoryCardProps {
  item: GameHistoryItem;
  delay?: number;
}

function HistoryCard({ item, delay = 0 }: HistoryCardProps) {
  const label = resultLabel(item);
  const cls = resultClass(item);
  const opponent = item.opponent_id;
  const navigate = useNavigate();

  const handleClick = () => {
    navigate(`/games/`);
  };

  return (
    <div
      className={`ug-hist-card ${cls}`}
      style={{ animationDelay: `${delay}ms` }}
      onClick={handleClick}
      onKeyDown={(e) => e.key === 'Enter' && handleClick()}
      role="button"
      tabIndex={0}
      aria-label={`Game vs ${opponent} — ${label}`}
    >
      {/* 左侧色条 */}
      <div className="ug-hist-card__accent" aria-hidden />

      {/* 我方 vs 对手 */}
      <div className="ug-hist-card__players">
        <div className="ug-hist-card__player">
          <span className={`ug-hist-card__piece ug-hist-card__piece--${item.your_color}`}>
            {item.your_color === 'white' ? '♔' : '♚'}
          </span>
          <span className="ug-hist-card__name">You</span>
        </div>
        <div className="ug-hist-card__player">
          <span className={`ug-hist-card__piece ug-hist-card__piece--${item.your_color === 'white' ? 'black' : 'white'}`}>
            {item.your_color === 'white' ? '♚' : '♔'}
          </span>
          <span className="ug-hist-card__name">{opponent}</span>
        </div>
      </div>

      {/* 结果 */}
      <div className="ug-hist-card__result">{label}</div>

      {/* 元信息 */}
      <div className="ug-hist-card__meta">
        <span className="ug-hist-card__tc">{formatTC(item.time_control)}</span>
        <span className="ug-hist-card__moves">{item.move_count} moves</span>
        <span className="ug-hist-card__date">{formatDate(item.created_at)}</span>
      </div>
    </div>
  );
}

// ---- 列表容器 ------------------------------------------------

interface HistoryListProps {
  games: GameHistoryItem[];
  isLoading: boolean;
  hasMore: boolean;
  error: string | null;
  onLoadMore: () => void;
}

export function HistoryList({
  games,
  isLoading,
  hasMore,
  error,
  onLoadMore,
}: HistoryListProps) {
  // 哨兵元素触发无限滚动
  const sentinelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = sentinelRef.current;
    if (!el) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !isLoading) {
          onLoadMore();
        }
      },
      { rootMargin: '120px' },
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [hasMore, isLoading, onLoadMore]);

  if (!isLoading && games.length === 0 && !error) {
    return (
      <div className="ug-hist-empty">
        <div className="ug-hist-empty__icon">♟</div>
        <p className="ug-hist-empty__text">No games yet. Play your first game!</p>
      </div>
    );
  }

  return (
    <div className="ug-hist-list">
      {games.map((g, i) => (
        <HistoryCard key={g.game_id} item={g} delay={Math.min(i * 30, 300)} />
      ))}

      {/* 加载状态 */}
      {isLoading && (
        <div className="ug-hist-loading">
          <div className="explorer-loading">
            <div className="explorer-loading__dot" />
            <div className="explorer-loading__dot" />
            <div className="explorer-loading__dot" />
          </div>
        </div>
      )}

      {/* 错误 */}
      {error && (
        <div className="ug-hist-error">{error}</div>
      )}

      {/* 无限滚动哨兵 */}
      <div ref={sentinelRef} style={{ height: 1 }} />
    </div>
  );
}
