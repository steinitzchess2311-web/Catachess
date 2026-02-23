// ============================================================
// PlayPage — 游戏大厅
// 路由：/play
//
// 左：创建新对局
// 右：历史对局列表
// 顶部：访客提示条（未登录时显示）
// ============================================================

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { usePlayerId } from './hooks/useGuestId';
import { useGameHistory } from './hooks/useGameHistory';
import { GameLobby } from './components/GameLobby';
import { HistoryList } from './components/HistoryList';

interface PlayPageProps {
  /** 已登录用户名（未登录传 null）*/
  username: string | null;
}

export function PlayPage({ username }: PlayPageProps) {
  const navigate = useNavigate();
  const myId = usePlayerId(username);
  const isGuest = !username;

  const { games, isLoading, hasMore, error, loadMore } = useGameHistory(myId);

  const handleGameCreated = (gameId: string) => {
    navigate(`/chess/${gameId}`);
  };

  return (
    <div className="ug-page ug-play-page">
      {/* 访客提示条 */}
      {isGuest && (
        <div className="ug-guest-banner">
          <span>Playing as guest — game history is saved locally only.</span>
          <a href="/login" className="ug-guest-banner__link">Sign in</a>
          {' '}to save your games permanently.
        </div>
      )}

      <div className="ug-play-layout">
        {/* ---- 左：创建对局 ---- */}
        <div className="ug-play-lobby-col">
          <GameLobby myId={myId} onGameCreated={handleGameCreated} />
        </div>

        {/* ---- 右：历史对局 ---- */}
        <div className="ug-play-history-col">
          <div className="ug-play-history-header">
            <h2 className="ug-play-history-title">Recent Games</h2>
          </div>
          <HistoryList
            games={games}
            isLoading={isLoading}
            hasMore={hasMore}
            error={error}
            onLoadMore={loadMore}
          />
        </div>
      </div>
    </div>
  );
}
