// ============================================================
// user_games — API 封装
// 所有 HTTP 请求统一在此，组件不直接 fetch
// ============================================================

import type {
  CreateGameResponse,
  CreateOpenGameResponse,
  CurrentGameResponse,
  GameDetail,
  GameListResponse,
  JoinGameResponse,
  TimeControl,
} from './types';

// ---- 业务错误（含服务端 error code）--------------------------

export class GameApiError extends Error {
  constructor(
    public readonly code: string,
    message: string,
    public readonly currentGameId?: string,
  ) {
    super(message);
    this.name = 'GameApiError';
  }
}

const BASE = 'https://gameserver.catachess.com';

// ---- 工具函数 -----------------------------------------------

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const code: string = body?.detail?.error ?? 'unknown';
    const message: string =
      body?.detail?.message ?? body?.message ?? `HTTP ${res.status}`;
    const currentGameId: string | undefined = body?.detail?.current_game_id;
    throw new GameApiError(code, message, currentGameId);
  }

  return res.json();
}

// ---- 健康检查 -----------------------------------------------

export async function checkHealth(): Promise<boolean> {
  try {
    const data = await request<{ status: string }>('/health');
    return data.status === 'ok';
  } catch {
    return false;
  }
}

// ---- 创建对局 -----------------------------------------------

export async function createGame(
  playerId: string,
  opponentId: string,
  timeControl: TimeControl = { initial: 300, increment: 3 },
  colorPreference: 'white' | 'black' | 'random' = 'random',
): Promise<CreateGameResponse> {
  return request<CreateGameResponse>('/api/game/create', {
    method: 'POST',
    body: JSON.stringify({
      player_id: playerId,
      opponent_id: opponentId,
      time_control: timeControl,
      color_preference: colorPreference,
    }),
  });
}

// ---- 创建开放对局（无需指定对手，生成分享链接）---------------

export async function createOpenGame(
  playerId: string,
  timeControl: TimeControl = { initial: 300, increment: 3 },
): Promise<CreateOpenGameResponse> {
  return request<CreateOpenGameResponse>('/api/game/create-open', {
    method: 'POST',
    body: JSON.stringify({
      player_id: playerId,
      time_control: timeControl,
    }),
  });
}

// ---- 加入开放对局 -------------------------------------------

/**
 * 加入处于 open 状态的对局。
 * - userId 有值 → 已登录/访客 ID
 * - userId 为 undefined → 匿名，服务端生成 anon_user_id，
 *   前端必须将其持久化用于 WS 连接
 */
export async function joinGame(
  gameId: string,
  userId?: string,
): Promise<JoinGameResponse> {
  return request<JoinGameResponse>(`/api/game/${gameId}/join`, {
    method: 'POST',
    body: JSON.stringify(userId ? { user_id: userId } : {}),
  });
}

// ---- 获取当前进行中对局（用于断线重连）-----------------------

export async function getCurrentGame(
  userId: string,
): Promise<CurrentGameResponse | null> {
  return request<CurrentGameResponse | null>(
    `/api/game/current?user_id=${encodeURIComponent(userId)}`
  );
}

// ---- 对局详情 -----------------------------------------------

export async function getGameDetail(gameId: string): Promise<GameDetail> {
  return request<GameDetail>(`/api/game/${gameId}`);
}

// ---- 历史对局列表（游标分页）---------------------------------

export async function listGames(
  userId: string,
  limit = 20,
  cursor?: string,
): Promise<GameListResponse> {
  const url = new URL(`${BASE}/api/game/list`);
  url.searchParams.set('user_id', userId);
  url.searchParams.set('limit', String(limit));
  if (cursor) url.searchParams.set('cursor', cursor);

  const res = await fetch(url.toString());
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.message ?? `HTTP ${res.status}`);
  }
  return res.json();
}

// ---- 中止对局 -----------------------------------------------

export async function abortGame(
  gameId: string,
  userId: string,
): Promise<void> {
  await request(`/api/game/${gameId}/abort`, {
    method: 'POST',
    body: JSON.stringify({ user_id: userId, reason: 'user_request' }),
  });
}

// ---- 导出 PGN -----------------------------------------------

export async function fetchGamePgn(gameId: string): Promise<string> {
  const res = await fetch(`${BASE}/api/game/${gameId}/pgn`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.text();
}

// ---- WebSocket URL 拼接 -------------------------------------

/**
 * 注意：API 文档返回的 ws_url 是内网地址，前端不用，
 * 统一用此函数拼接正确的 wss 地址
 */
export function buildWsUrl(gameId: string, userId: string): string {
  return `wss://gameserver.catachess.com/ws/game/${gameId}?user_id=${encodeURIComponent(userId)}`;
}
