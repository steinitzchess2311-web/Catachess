// ============================================================
// AnalyzeGamePage — 赛后分析跳板
// 路由：/chess/:gameId/analyze
//
// 职责：拉取 PGN + 对局元信息 → 跳转到 /analysis
// 分析页面本身（布局、引擎、Explorer）完全由 /analysis 提供
// ============================================================

import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { fetchGamePgn, getGameDetail } from './api';

// ---- 加载 / 错误状态 ----------------------------------------

function LoadingScreen() {
  return (
    <div className="ug-page ug-page--loading">
      <div className="ug-connecting">
        <div className="explorer-loading">
          <div className="explorer-loading__dot" />
          <div className="explorer-loading__dot" />
          <div className="explorer-loading__dot" />
        </div>
        <span>Loading game analysis…</span>
      </div>
    </div>
  );
}

function ErrorScreen({ message }: { message: string }) {
  const navigate = useNavigate();
  return (
    <div className="ug-page ug-page--error">
      <div className="ug-error-card">
        <p>{message}</p>
        <button
          type="button"
          className="ug-error-card__btn"
          onClick={() => navigate(-1)}
        >
          Go Back
        </button>
      </div>
    </div>
  );
}

// ---- 页面入口 -----------------------------------------------

export function AnalyzeGamePage() {
  const { gameId } = useParams<{ gameId: string }>();
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!gameId) return;

    Promise.all([
      fetchGamePgn(gameId),
      getGameDetail(gameId),
    ])
      .then(([pgn, game]) => {
        navigate('/analysis', {
          replace: true,
          state: {
            pgn,
            gameContext: {
              gameId,
              white: game.white_player_id,
              black: game.black_player_id ?? '?',
              result: game.result,
              timeControl: game.time_control,
              backUrl: `/chess/${gameId}`,
            },
          },
        });
      })
      .catch((e) => {
        setError(e instanceof Error ? e.message : 'Failed to load game');
      });
  }, [gameId, navigate]);

  if (error) return <ErrorScreen message={error} />;
  return <LoadingScreen />;
}
