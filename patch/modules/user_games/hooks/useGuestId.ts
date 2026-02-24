// ============================================================
// useGuestId — 为未登录用户生成/复用持久化访客 ID
// 存在 localStorage，刷新不消失，清缓存则重新生成
// ============================================================

import { useMemo } from 'react';

const GUEST_KEY = 'cata_guest_id';

/** 生成随机 guest ID，格式：guest_xxxxxx（6位小写字母数字）*/
function generateGuestId(): string {
  const chars = 'abcdefghijklmnopqrstuvwxyz0123456789';
  let id = 'guest_';
  for (let i = 0; i < 6; i++) {
    id += chars[Math.floor(Math.random() * chars.length)];
  }
  return id;
}

/** 读取或创建 guest ID */
export function getOrCreateGuestId(): string {
  try {
    const existing = localStorage.getItem(GUEST_KEY);
    if (existing) return existing;
    const fresh = generateGuestId();
    localStorage.setItem(GUEST_KEY, fresh);
    return fresh;
  } catch {
    // localStorage 不可用时（隐身模式等）临时生成
    return generateGuestId();
  }
}

/**
 * 返回当前用户 ID：
 * - 已登录：使用传入的 username
 * - 未登录：使用 localStorage 中的 guest ID
 */
export function usePlayerId(username: string | null): string {
  return useMemo(() => {
    if (username) return username;
    return getOrCreateGuestId();
  }, [username]);
}

// ---- 匿名加入对局的 ID（按 game 维度存储）-------------------
// 通过分享链接匿名加入时，服务端返回 anon_user_id，
// 前端必须按 gameId 保存，用于后续 WS 连接和断线重连。

const ANON_GAME_PREFIX = 'cata_anon_';

/** 保存匿名加入某局的 anon_user_id（存入 sessionStorage）*/
export function saveAnonIdForGame(gameId: string, anonId: string): void {
  try {
    sessionStorage.setItem(ANON_GAME_PREFIX + gameId, anonId);
  } catch { /* ignore */ }
}

/** 读取匿名加入某局保存的 ID，无则返回 null */
export function getAnonIdForGame(gameId: string): string | null {
  try {
    return sessionStorage.getItem(ANON_GAME_PREFIX + gameId);
  } catch {
    return null;
  }
}
