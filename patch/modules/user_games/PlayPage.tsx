// ============================================================
// PlayPage — 游戏大厅
// Route: /games
//
// 只负责发起挑战（历史对局已移到 /@username 个人主页）
// ============================================================

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { usePlayerId } from './hooks/useGuestId';
import { GameLobby } from './components/GameLobby';

interface PlayPageProps {
  /** 已登录用户名（未登录传 null）*/
  username: string | null;
}

export function PlayPage({ username }: PlayPageProps) {
  const navigate = useNavigate();
  const myId = usePlayerId(username);
  const isGuest = !username;

  const handleGameCreated = (gameId: string) => {
    navigate(`/games/${gameId}`);
  };

  return (
    <div className="ug-page ug-play-page">
      {/* 访客提示条 */}
      {isGuest && (
        <div className="ug-guest-banner">
          <span>Playing as guest — your game history won't be saved.</span>
          <a href="/login" className="ug-guest-banner__link">Sign in</a>
          {' '}for a full experience.
        </div>
      )}

      <div className="ug-play-lobby-centered">
        <GameLobby myId={myId} onGameCreated={handleGameCreated} />
      </div>
    </div>
  );
}
