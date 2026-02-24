// ============================================================
// LiveGamePage — 实时对局室
// 路由：/chess/:gameId
//
// 布局：
//   左：棋盘 + 玩家信息栏 + 时钟
//   右：走法列表 + 对局操作按钮
// ============================================================

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Chess } from 'chess.js';
import { abortGame } from './api';
import { getAnonIdForGame, getOrCreateGuestId } from './hooks/useGuestId';
import { useGameWs } from './hooks/useGameWs';
import { LiveBoard } from './components/LiveBoard';
import { PlayerBar } from './components/PlayerBar';
import { DrawOfferBanner } from './components/DrawOfferBanner';
import { GameResultOverlay } from './components/GameResultOverlay';
import { MoveList } from './components/MoveList';
import { GameControls } from './components/GameControls';
import type { PlayerColor } from './types';

interface LiveGamePageProps {
  /** 已登录用户名（未登录传 null）*/
  username: string | null;
}

export function LiveGamePage({ username }: LiveGamePageProps) {
  const { gameId } = useParams<{ gameId: string }>();
  const navigate = useNavigate();

  // 当前用户 ID，优先级：
  //   1. 通过分享链接匿名加入时服务端返回的 anon_user_id（存于 sessionStorage）
  //   2. 已登录 username
  //   3. localStorage 中的 guest ID
  const myId = useMemo(() => {
    if (gameId) {
      const anonId = getAnonIdForGame(gameId);
      if (anonId) return anonId;
    }
    return username ?? getOrCreateGuestId();
  }, [gameId, username]);

  const {
    state,
    sendMove,
    sendResign,
    sendOfferDraw,
    sendAcceptDraw,
    sendDeclineDraw,
  } = useGameWs(gameId, myId);

  // ---- 走法历史回看 ------------------------------------------
  // null = 跟随最新局面；数字 = 查看历史第 n 步后的局面
  const [viewIndex, setViewIndex] = useState<number | null>(null);

  // 收到新走法时，若不在回看状态，自动跟随最新
  useEffect(() => {
    setViewIndex(null);
  }, [state.moves.length]);

  // 根据 viewIndex 计算实际显示的 FEN
  const displayFen = useMemo(() => {
    // 跟随最新
    if (viewIndex === null) return state.fen;

    // 回放到第 viewIndex 步
    const chess = new Chess();
    for (let i = 0; i <= viewIndex && i < state.moves.length; i++) {
      try {
        chess.move(state.moves[i]);
      } catch {
        break;
      }
    }
    return chess.fen();
  }, [viewIndex, state.fen, state.moves]);

  // 回看时棋盘锁定
  const isViewingHistory = viewIndex !== null;

  // ---- 键盘快捷键（←→ 翻阅走法）---------------------------
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      if (target.closest('input, textarea')) return;

      if (e.key === 'ArrowLeft') {
        e.preventDefault();
        setViewIndex((prev) => {
          const cur = prev ?? state.moves.length - 1;
          return cur <= 0 ? null : cur - 1;
        });
      } else if (e.key === 'ArrowRight') {
        e.preventDefault();
        setViewIndex((prev) => {
          if (prev === null) return null;
          const next = prev + 1;
          return next >= state.moves.length - 1 ? null : next;
        });
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [state.moves.length]);

  // ---- 中止对局 ----------------------------------------------
  const handleAbort = useCallback(async () => {
    if (!gameId) return;
    try {
      await abortGame(gameId, myId);
    } catch {
      // 服务器也会推 game_over，这里静默处理
    }
  }, [gameId, myId]);

  // ---- 判断各方颜色 ------------------------------------------
  const myColor = state.myColor;
  const opponentColor: PlayerColor | null = myColor
    ? myColor === 'white' ? 'black' : 'white'
    : null;

  // 上方玩家（对手），下方玩家（自己）
  const topId = myColor === 'white' ? state.blackId : state.whiteId;
  const bottomId = myColor === 'white' ? state.whiteId : state.blackId;
  const topColor: PlayerColor = myColor === 'white' ? 'black' : 'white';
  const bottomColor: PlayerColor = myColor === 'white' ? 'white' : 'black';
  const topMs = topColor === 'white' ? state.clockWhite : state.clockBlack;
  const bottomMs = bottomColor === 'white' ? state.clockWhite : state.clockBlack;
  const topActive = state.turn === topColor && state.phase === 'ongoing';
  const bottomActive = state.turn === bottomColor && state.phase === 'ongoing';
  const isOver = state.phase === 'over';

  // ---- 已完成对局自动跳转分析页 ------------------------------
  // phase=over 且没有通过 WS 收到任何数据（result=null, moves=0）
  // 说明连接的是已结束的历史对局，直接跳分析页
  useEffect(() => {
    if (state.phase === 'over' && state.result === null && state.moves.length === 0 && gameId) {
      navigate(`/chess/${gameId}/analyze`, { replace: true });
    }
  }, [state.phase, state.result, state.moves.length, gameId, navigate]);

  // ---- 连接状态渲染 ------------------------------------------
  if (state.phase === 'connecting') {
    return (
      <div className="ug-page ug-page--loading">
        <div className="ug-connecting">
          <div className="explorer-loading">
            <div className="explorer-loading__dot" />
            <div className="explorer-loading__dot" />
            <div className="explorer-loading__dot" />
          </div>
          <span>Connecting to game...</span>
        </div>
      </div>
    );
  }

  if (state.phase === 'disconnected') {
    return (
      <div className="ug-page ug-page--error">
        <div className="ug-error-card">
          <p>Connection lost.</p>
          <button
            type="button"
            className="ug-error-card__btn"
            onClick={() => window.location.reload()}
          >
            Reconnect
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="ug-page ug-game-page">
      {/* 等待对手连接提示 */}
      {state.phase === 'waiting' && (
        <div className="ug-waiting-banner">
          Waiting for opponent to connect...
        </div>
      )}

      {/* 提和通知条 */}
      <DrawOfferBanner
        incoming={state.drawOffer.incoming}
        outgoing={state.drawOffer.outgoing}
        onAccept={sendAcceptDraw}
        onDecline={sendDeclineDraw}
      />

      <div className="ug-game-layout">
        {/* ---- 左栏：棋盘 + 玩家信息 ---- */}
        <div className="ug-game-board-col">
          {/* 对手信息栏（棋盘上方）*/}
          <PlayerBar
            playerId={topId || '—'}
            color={topColor}
            timeMs={topMs}
            isActive={topActive}
            isOver={isOver}
            isMe={false}
            isDisconnected={state.opponentDisconnected}
          />

          {/* 棋盘（相对定位，结算层叠其上）*/}
          <div className="ug-board-container">
            <LiveBoard
              fen={displayFen}
              myColor={myColor}
              turn={state.turn}
              isOver={isOver || isViewingHistory}
              onMove={(from, to, promo) => {
                // 回看状态下不允许走棋
                if (!isViewingHistory) sendMove(from, to, promo);
              }}
            />

            {/* 对局结束覆盖层 */}
            {isOver && state.result && gameId && (
              <GameResultOverlay
                result={state.result}
                myColor={myColor}
                gameId={gameId}
                onNewGame={() => navigate('/play')}
              />
            )}
          </div>

          {/* 我的信息栏（棋盘下方）*/}
          <PlayerBar
            playerId={bottomId || myId}
            color={bottomColor}
            timeMs={bottomMs}
            isActive={bottomActive}
            isOver={isOver}
            isMe
          />
        </div>

        {/* ---- 右栏：走法列表 + 操作按钮 ---- */}
        <div className="ug-game-side-col">
          <div className="ug-game-side-panel">
            {/* 走法列表 */}
            <div className="ug-game-moves-wrap">
              <MoveList
                moves={state.moves}
                viewIndex={viewIndex}
                onSelectMove={setViewIndex}
              />
            </div>

            {/* 操作按钮 */}
            <GameControls
              phase={state.phase}
              moveCount={state.moves.length}
              hasOutgoingDraw={state.drawOffer.outgoing}
              onResign={sendResign}
              onOfferDraw={sendOfferDraw}
              onAbort={handleAbort}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
