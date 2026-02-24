// ============================================================
// JoinGamePage — 通过分享链接加入开放对局
// 路由：/chess/:gameId/join
//
// 流程：
//   1. 加载对局信息（创建者、时间控制、状态）
//   2. 用户点击 "Join" → 调用 POST /api/game/{id}/join
//   3. 匿名用户：持久化 anon_user_id 到 sessionStorage
//   4. 短暂展示颜色分配 → 自动跳转至 /chess/:gameId
// ============================================================

import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { GameApiError, getGameDetail, joinGame } from './api';
import { saveAnonIdForGame } from './hooks/useGuestId';
import type { GameDetail, PlayerColor } from './types';

interface JoinGamePageProps {
  /** 已登录用户名（未登录传 null）*/
  username: string | null;
}

// ---- 页面阶段 -----------------------------------------------
type Phase =
  | { kind: 'loading' }
  | { kind: 'open';    game: GameDetail }
  | { kind: 'joining' }
  | { kind: 'joined';  myColor: PlayerColor; opponent: string; gameId: string }
  | { kind: 'already_started'; gameId: string }
  | { kind: 'own_game' }
  | { kind: 'expired' }
  | { kind: 'not_found' }
  | { kind: 'error';   message: string };

// ---- 工具 ---------------------------------------------------

function formatTimeControl(initial: number, increment: number): string {
  const mins = Math.floor(initial / 60);
  const secs = initial % 60;
  const timeStr = secs > 0 ? `${mins}:${String(secs).padStart(2, '0')}` : String(mins);
  return `${timeStr}+${increment}`;
}

function tcCategory(initial: number): string {
  if (initial <= 180)  return 'Bullet';
  if (initial <= 600)  return 'Blitz';
  if (initial <= 1800) return 'Rapid';
  return 'Classical';
}

// ---- 主组件 -------------------------------------------------

export function JoinGamePage({ username }: JoinGamePageProps) {
  const { gameId } = useParams<{ gameId: string }>();
  const navigate = useNavigate();
  const [phase, setPhase] = useState<Phase>({ kind: 'loading' });
  const [redirectCountdown, setRedirectCountdown] = useState(3);

  // ---- 加载对局信息 ------------------------------------------
  useEffect(() => {
    if (!gameId) {
      setPhase({ kind: 'not_found' });
      return;
    }

    getGameDetail(gameId)
      .then((game) => {
        if (game.status === 'open') {
          // 检查是否是自己创建的对局
          if (game.created_by && username && game.created_by === username) {
            setPhase({ kind: 'own_game' });
            return;
          }
          setPhase({ kind: 'open', game });
        } else if (game.status === 'waiting' || game.status === 'ongoing') {
          setPhase({ kind: 'already_started', gameId });
        } else if (game.status === 'aborted') {
          setPhase({ kind: 'expired' });
        } else {
          // completed — 重定向到分析页
          setPhase({ kind: 'already_started', gameId });
        }
      })
      .catch((err) => {
        if (err instanceof GameApiError && err.code === 'game_not_found') {
          setPhase({ kind: 'not_found' });
        } else {
          setPhase({ kind: 'error', message: err instanceof Error ? err.message : 'Unknown error' });
        }
      });
  }, [gameId, username]);

  // ---- 倒计时跳转 --------------------------------------------
  useEffect(() => {
    if (phase.kind !== 'joined') return;

    const iv = setInterval(() => {
      setRedirectCountdown((n) => {
        if (n <= 1) {
          clearInterval(iv);
          navigate(`/chess/${phase.gameId}`, { replace: true });
          return 0;
        }
        return n - 1;
      });
    }, 1000);

    return () => clearInterval(iv);
  }, [phase, navigate]);

  // ---- 加入对局 -----------------------------------------------
  const handleJoin = async () => {
    if (!gameId) return;
    setPhase({ kind: 'joining' });

    try {
      const res = await joinGame(gameId, username ?? undefined);

      // 匿名加入：持久化 anon_user_id
      if (res.anon_user_id) {
        saveAnonIdForGame(gameId, res.anon_user_id);
      }

      const effectiveId = username ?? res.anon_user_id ?? '';
      const myColor: PlayerColor =
        res.white_player_id === effectiveId ? 'white' : 'black';
      const opponent =
        myColor === 'white' ? res.black_player_id : res.white_player_id;

      setRedirectCountdown(3);
      setPhase({ kind: 'joined', myColor, opponent, gameId });

    } catch (err) {
      if (err instanceof GameApiError) {
        switch (err.code) {
          case 'game_already_started':
            setPhase({ kind: 'already_started', gameId });
            return;
          case 'game_expired':
            setPhase({ kind: 'expired' });
            return;
          case 'cannot_join_own_game':
            setPhase({ kind: 'own_game' });
            return;
          case 'game_not_found':
            setPhase({ kind: 'not_found' });
            return;
        }
      }
      setPhase({ kind: 'error', message: err instanceof Error ? err.message : 'Join failed.' });
    }
  };

  // ================================================================
  // Render
  // ================================================================

  return (
    <div className="ug-page ug-join-page">
      <div className="ug-join-card">

        {/* ---- 加载中 ---- */}
        {phase.kind === 'loading' && (
          <div className="ug-join-state ug-join-state--loading">
            <div className="ug-lobby__spinner" />
            <span>Loading game…</span>
          </div>
        )}

        {/* ---- 可加入 ---- */}
        {phase.kind === 'open' && (
          <>
            <div className="ug-join-header">
              <span className="ug-join-icon">♟</span>
              <h2 className="ug-join-title">Chess Challenge</h2>
              <p className="ug-join-subtitle">
                <strong>{phase.game.created_by ?? 'Someone'}</strong> is looking for an opponent
              </p>
            </div>

            <div className="ug-join-tc">
              <span className="ug-join-tc__time">
                {formatTimeControl(
                  phase.game.time_control.initial,
                  phase.game.time_control.increment
                )}
              </span>
              <span className="ug-join-tc__cat">
                {tcCategory(phase.game.time_control.initial)}
              </span>
            </div>

            {!username && (
              <div className="ug-join-anon-note">
                You're joining as a guest — your game won't be saved to any account.{' '}
                <a href="/login" className="ug-join-anon-note__link">Sign in</a> for full features.
              </div>
            )}

            <button
              type="button"
              className="ug-lobby__submit ug-join-btn"
              onClick={handleJoin}
            >
              Join Game
            </button>
          </>
        )}

        {/* ---- 加入中 ---- */}
        {phase.kind === 'joining' && (
          <div className="ug-join-state">
            <div className="ug-lobby__spinner" />
            <span>Joining game…</span>
          </div>
        )}

        {/* ---- 加入成功 ---- */}
        {phase.kind === 'joined' && (
          <div className="ug-join-success">
            <div className="ug-join-success__check">✓</div>
            <h2 className="ug-join-title">You're in!</h2>

            <div className="ug-join-color-badge">
              <span className={`ug-join-color-icon ug-join-color-icon--${phase.myColor}`}>
                {phase.myColor === 'white' ? '♔' : '♚'}
              </span>
              <span>
                You play as <strong>{phase.myColor === 'white' ? 'White' : 'Black'}</strong>
              </span>
            </div>

            <p className="ug-join-vs">vs <strong>{phase.opponent}</strong></p>

            <p className="ug-join-redirect">
              Entering game in <strong>{redirectCountdown}</strong>s…
            </p>

            <button
              type="button"
              className="ug-lobby__submit ug-join-btn"
              onClick={() => navigate(`/chess/${phase.gameId}`, { replace: true })}
            >
              Go Now
            </button>
          </div>
        )}

        {/* ---- 对局已开始 ---- */}
        {phase.kind === 'already_started' && (
          <div className="ug-join-state">
            <span className="ug-join-state__icon">♟</span>
            <h3>Game already started</h3>
            <p>This game is currently in progress.</p>
            <button
              type="button"
              className="ug-lobby__submit ug-join-btn"
              onClick={() => navigate(`/chess/${phase.gameId}`)}
            >
              Watch Game
            </button>
          </div>
        )}

        {/* ---- 自己的对局 ---- */}
        {phase.kind === 'own_game' && (
          <div className="ug-join-state">
            <span className="ug-join-state__icon">👋</span>
            <h3>That's your game!</h3>
            <p>Share the link with a friend — you can't play against yourself.</p>
            <button
              type="button"
              className="ug-lobby__submit ug-join-btn"
              onClick={() => navigate('/play')}
            >
              Back to Lobby
            </button>
          </div>
        )}

        {/* ---- 链接过期 ---- */}
        {phase.kind === 'expired' && (
          <div className="ug-join-state">
            <span className="ug-join-state__icon">⏱</span>
            <h3>Link expired</h3>
            <p>This invite link is no longer valid (10-minute window).</p>
            <button
              type="button"
              className="ug-lobby__submit ug-join-btn"
              onClick={() => navigate('/play')}
            >
              Create Your Own Game
            </button>
          </div>
        )}

        {/* ---- 对局不存在 ---- */}
        {phase.kind === 'not_found' && (
          <div className="ug-join-state">
            <span className="ug-join-state__icon">🔍</span>
            <h3>Game not found</h3>
            <p>This link doesn't match any game. It may have been deleted.</p>
            <button
              type="button"
              className="ug-lobby__submit ug-join-btn"
              onClick={() => navigate('/play')}
            >
              Go to Lobby
            </button>
          </div>
        )}

        {/* ---- 通用错误 ---- */}
        {phase.kind === 'error' && (
          <div className="ug-join-state">
            <span className="ug-join-state__icon">⚠</span>
            <h3>Something went wrong</h3>
            <p className="ug-join-state__msg">{phase.message}</p>
            <button
              type="button"
              className="ug-lobby__submit ug-join-btn"
              onClick={() => navigate('/play')}
            >
              Go to Lobby
            </button>
          </div>
        )}

      </div>
    </div>
  );
}
