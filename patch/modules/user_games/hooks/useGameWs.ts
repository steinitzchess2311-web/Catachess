// ============================================================
// useGameWs — 实时对局 WebSocket 状态机（核心 hook）
//
// 状态流转：connecting → waiting → ongoing → over
// 所有 WS 消息在此统一处理，组件只消费 state
// ============================================================

import { useCallback, useEffect, useRef, useState } from 'react';
import { buildWsUrl } from '../api';
import type {
  ClientMessage,
  DrawOfferState,
  GamePhase,
  GameResult,
  LiveGameState,
  PlayerColor,
  ServerMessage,
} from '../types';

const INITIAL_FEN = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1';
const HEARTBEAT_INTERVAL_MS = 25_000; // 每 25 秒发一次 ping

// ---- 初始状态 -----------------------------------------------

function makeInitialState(): LiveGameState {
  return {
    phase: 'connecting',
    fen: INITIAL_FEN,
    turn: 'white',
    myColor: null,
    whiteId: '',
    blackId: '',
    clockWhite: 0,
    clockBlack: 0,
    moves: [],
    drawOffer: { incoming: false, outgoing: false },
    result: null,
    opponentDisconnected: false,
    error: null,
  };
}

// ---- hook ---------------------------------------------------

export interface UseGameWsReturn {
  state: LiveGameState;
  /** 走棋（发送给服务器）*/
  sendMove: (from: string, to: string, promotion?: string) => void;
  sendResign: () => void;
  sendOfferDraw: () => void;
  sendAcceptDraw: () => void;
  sendDeclineDraw: () => void;
}

export function useGameWs(
  gameId: string | undefined,
  userId: string,
): UseGameWsReturn {
  const [state, setState] = useState<LiveGameState>(makeInitialState);

  const wsRef = useRef<WebSocket | null>(null);
  // 用 ref 同步最新 state，避免闭包过时
  const stateRef = useRef<LiveGameState>(state);
  stateRef.current = state;

  // ---- 发送工具函数 ------------------------------------------
  const send = useCallback((msg: ClientMessage) => {
    const ws = wsRef.current;
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(msg));
    }
  }, []);

  // ---- 消息处理器 --------------------------------------------
  const handleMessage = useCallback((raw: string) => {
    let msg: ServerMessage;
    try {
      msg = JSON.parse(raw);
    } catch {
      console.warn('[GameWs] 无法解析消息:', raw);
      return;
    }

    setState((prev) => {
      switch (msg.type) {
        // 连接后初始状态
        case 'game_state': {
          const clockWhite = Math.round(msg.time_remaining.white * 1000);
          const clockBlack = Math.round(msg.time_remaining.black * 1000);
          return {
            ...prev,
            phase: msg.status === 'waiting' ? 'waiting' : 'ongoing',
            fen: msg.fen,
            turn: msg.turn,
            myColor: msg.your_color,
            whiteId: msg.white_player_id,
            blackId: msg.black_player_id,
            clockWhite,
            clockBlack,
            moves: [],
            error: null,
          };
        }

        // 走棋广播
        case 'move_made': {
          const clockWhite = Math.round(msg.time_remaining.white * 1000);
          const clockBlack = Math.round(msg.time_remaining.black * 1000);
          return {
            ...prev,
            phase: 'ongoing',
            fen: msg.fen,
            turn: msg.turn,
            clockWhite,
            clockBlack,
            moves: [...prev.moves, msg.move.san],
            // 走棋后重置提和状态
            drawOffer: { incoming: false, outgoing: false },
          };
        }

        // 每秒时钟更新：服务器校正
        case 'time_update': {
          const clockWhite = Math.round(msg.time_remaining.white * 1000);
          const clockBlack = Math.round(msg.time_remaining.black * 1000);
          return { ...prev, clockWhite, clockBlack };
        }

        // 对局结束
        case 'game_over': {
          const result: GameResult = {
            result: msg.result,
            reason: msg.reason,
            winner: msg.winner,
          };
          return {
            ...prev,
            phase: 'over',
            result,
            drawOffer: { incoming: false, outgoing: false },
          };
        }

        // 对手提和
        case 'draw_offered': {
          return {
            ...prev,
            drawOffer: { ...prev.drawOffer, incoming: true },
          };
        }

        // 对手断线/重连
        case 'opponent_disconnected':
          return { ...prev, opponentDisconnected: true };
        case 'opponent_reconnected':
          return { ...prev, opponentDisconnected: false };

        // 服务器报错（走棋非法等）
        case 'error':
          return { ...prev, error: msg.message };

        // 心跳响应，忽略
        case 'pong':
          return prev;

        default:
          return prev;
      }
    });
  }, []);

  // ---- WebSocket 连接生命周期 --------------------------------
  useEffect(() => {
    if (!gameId) return;

    const url = buildWsUrl(gameId, userId);
    const ws = new WebSocket(url);
    wsRef.current = ws;

    setState(makeInitialState());

    ws.onopen = () => {
      // 连接建立，等待服务器推送 game_state
    };

    ws.onmessage = (event) => handleMessage(event.data);

    ws.onerror = () => {
      setState((prev) => ({ ...prev, phase: 'disconnected', error: 'Connection error' }));
    };

    ws.onclose = () => {
      setState((prev) => {
        // 如果已经 over，不覆盖状态
        if (prev.phase === 'over') return prev;
        return { ...prev, phase: 'disconnected' };
      });
    };

    // 心跳：防止 WebSocket 被代理/防火墙断开
    const heartbeat = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'ping' }));
      }
    }, HEARTBEAT_INTERVAL_MS);

    return () => {
      clearInterval(heartbeat);
      ws.close();
      wsRef.current = null;
    };
  }, [gameId, userId, handleMessage]);

  // ---- 对外动作 -----------------------------------------------

  const sendMove = useCallback(
    (from: string, to: string, promotion?: string) => {
      const msg: ClientMessage = promotion
        ? { type: 'move', from, to, promotion }
        : { type: 'move', from, to };
      send(msg);
    },
    [send],
  );

  const sendResign = useCallback(() => send({ type: 'resign' }), [send]);

  const sendOfferDraw = useCallback(() => {
    send({ type: 'offer_draw' });
    setState((prev) => ({
      ...prev,
      drawOffer: { ...prev.drawOffer, outgoing: true },
    }));
  }, [send]);

  const sendAcceptDraw = useCallback(() => {
    send({ type: 'accept_draw' });
    setState((prev) => ({
      ...prev,
      drawOffer: { incoming: false, outgoing: false },
    }));
  }, [send]);

  const sendDeclineDraw = useCallback(() => {
    send({ type: 'decline_draw' });
    setState((prev) => ({
      ...prev,
      drawOffer: { ...prev.drawOffer, incoming: false },
    }));
  }, [send]);

  return {
    state,
    sendMove,
    sendResign,
    sendOfferDraw,
    sendAcceptDraw,
    sendDeclineDraw,
  };
}
