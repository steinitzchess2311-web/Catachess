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
