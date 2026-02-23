// ============================================================
// PlayerPage — 棋手对局检索主页
// ============================================================

import React, { useState, useCallback } from 'react';
import './player.css';
import { PlayerSearchInput } from './components/PlayerSearchInput';
import { FilterBar } from './components/FilterBar';
import { GameList } from './components/GameList';
import { usePlayerGames } from './hooks/usePlayerGames';
import { DEFAULT_FILTERS } from './types';
import type { SearchFilters } from './types';

function HeroIllustration() {
  return (
    <svg className="ps-hero-board" viewBox="0 0 120 120" fill="none" aria-hidden>
      {/* 棋盘格 */}
      {[0,1,2,3,4,5,6,7].map(r =>
        [0,1,2,3,4,5,6,7].map(c => (
          <rect
            key={`${r}-${c}`}
            x={c * 15}
            y={r * 15}
            width={15}
            height={15}
            fill={(r + c) % 2 === 0 ? 'rgba(255,255,255,0.08)' : 'transparent'}
          />
        ))
      )}
      {/* 几个棋子示意 */}
      <text x="22" y="48" fontSize="18" textAnchor="middle" fill="rgba(255,255,255,0.7)">♛</text>
      <text x="52" y="78" fontSize="18" textAnchor="middle" fill="rgba(255,255,255,0.4)">♞</text>
      <text x="82" y="38" fontSize="18" textAnchor="middle" fill="rgba(255,255,255,0.6)">♜</text>
      <text x="37" y="103" fontSize="18" textAnchor="middle" fill="rgba(255,255,255,0.3)">♝</text>
      <text x="97" y="68" fontSize="18" textAnchor="middle" fill="rgba(255,255,255,0.5)">♚</text>
    </svg>
  );
}

const PlayerPage: React.FC = () => {
  const [player, setPlayer] = useState('');
  const [filters, setFilters] = useState<SearchFilters>(DEFAULT_FILTERS);

  // 切换棋手时重置过滤器
  const handleSearch = useCallback((name: string) => {
    setPlayer(name);
    setFilters(DEFAULT_FILTERS);
  }, []);

  const handleFiltersChange = useCallback((f: SearchFilters) => {
    setFilters(f);
  }, []);

  const { games, loading, error, hasMore, total, loadMore } = usePlayerGames(player, filters);

  const hasResults = games.length > 0 || loading;

  return (
    <div className="ps-page">
      {/* Hero */}
      <div className="ps-hero">
        <HeroIllustration />
        <div className="ps-hero-content">
          <p className="ps-hero-eyebrow">Master Database · 460 万局</p>
          <h1 className="ps-hero-title">棋手对局检索</h1>
          <p className="ps-hero-desc">
            搜索任意大师棋手的全部对局，按年份、结果、颜色精确筛选。
          </p>
          <PlayerSearchInput onSearch={handleSearch} />
        </div>
      </div>

      {/* 结果区域 */}
      {(player || hasResults) && (
        <div className="ps-results">
          <div className="ps-results-inner">
            {/* 过滤器 */}
            {player && (
              <div className="ps-results-header">
                <div className="ps-results-title">
                  <span className="ps-results-player">{player}</span>
                  {!loading && games.length > 0 && (
                    <span className="ps-results-count">· {total}{hasMore ? '+' : ''} 局</span>
                  )}
                </div>
                <FilterBar filters={filters} onChange={handleFiltersChange} />
              </div>
            )}

            {/* 空状态 */}
            {!loading && !error && player && games.length === 0 && (
              <div className="ps-empty">
                <span className="ps-empty-icon">♟</span>
                <p>未找到符合条件的对局</p>
                <p className="ps-empty-hint">尝试修改过滤条件，或检查棋手姓名拼写</p>
              </div>
            )}

            {/* 对局列表 */}
            <GameList
              games={games}
              loading={loading}
              error={error}
              hasMore={hasMore}
              total={total}
              onLoadMore={loadMore}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default PlayerPage;
