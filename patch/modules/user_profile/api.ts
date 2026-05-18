// ============================================================
// user_profile — API 封装
// ============================================================

import { api } from '@ui/assets/api';
import type { EditableProfile, PublicActivity, PublicProfile } from './types';

/**
 * 获取指定用户的公开资料
 * 后端接口：GET /user/profile/{username}（见 need_backend.md #4）
 * 当前后端还没有这个接口，先用 /user/profile 做降级处理
 */
/**
 * 获取用户公开资料。
 *
 * 策略（按优先级）：
 *  1. 先尝试 GET /user/profile/{username}（后端实现后自动生效）
 *  2. 失败时降级到 GET /user/profile（只对当前登录用户有效）
 *  3. 两者都失败则返回只含 username 的最小资料，保证页面可渲染
 */
export async function fetchPublicProfile(username: string): Promise<PublicProfile> {
  const normalize = (data: Record<string, unknown>, fallbackUsername: string): PublicProfile => ({
    username: (data.username as string) ?? fallbackUsername,
    fide_title: (data.fide_title as string) ?? null,
    fide_rating: data.fide_rating ? Number(data.fide_rating) : null,
    cfc_rating: data.cfc_rating ? Number(data.cfc_rating) : null,
    ecf_rating: data.ecf_rating ? Number(data.ecf_rating) : null,
    chinese_athlete_title: (data.chinese_athlete_title as string) ?? null,
    lichess_username: (data.lichess_username as string) ?? null,
    chesscom_username: (data.chesscom_username as string) ?? null,
    self_intro: (data.self_intro as string) ?? null,
  });

  // 1. 尝试公开接口（后端实现后直接生效）
  try {
    const data = await api.get(`/user/profile/${username}`);
    return normalize(data, username);
  } catch {
    // 公开接口不存在，继续降级
  }

  // 2. 降级：用当前登录用户自己的接口（只有看自己的页面时有数据）
  try {
    const data = await api.get('/user/profile');
    // 只有返回的 username 匹配时才用，否则说明在看别人的页面
    if (data.username === username || data.username?.toLowerCase() === username.toLowerCase()) {
      return normalize(data, username);
    }
  } catch {
    // 未登录或接口失败，继续
  }

  // 3. 最终降级：只显示用户名，其余字段等后端接口就绪后填入
  return {
    username,
    fide_title: null,
    fide_rating: null,
    cfc_rating: null,
    ecf_rating: null,
    chinese_athlete_title: null,
    lichess_username: null,
    chesscom_username: null,
    self_intro: null,
  };
}

function normalizeActivity(raw: Record<string, unknown>, index: number): PublicActivity {
  const type = String(raw.event_type ?? raw.type ?? raw.kind ?? 'activity');
  const summary =
    typeof raw.summary === 'string' && raw.summary.trim()
      ? raw.summary
      : activitySummary(type, raw);

  return {
    id: String(raw.event_id ?? raw.id ?? `${type}-${index}`),
    type,
    summary,
    occurred_at: String(raw.occurred_at ?? raw.created_at ?? raw.updated_at ?? new Date().toISOString()),
    target_title: typeof raw.target_title === 'string' ? raw.target_title : typeof raw.title === 'string' ? raw.title : null,
    target_url: typeof raw.target_url === 'string' ? raw.target_url : typeof raw.url === 'string' ? raw.url : null,
  };
}

function activitySummary(type: string, raw: Record<string, unknown>): string {
  const normalizedType = type.toLowerCase();
  const title = typeof raw.title === 'string' ? raw.title : typeof raw.target_title === 'string' ? raw.target_title : '';
  if (normalizedType.includes('discussion') || normalizedType.includes('comment')) return title ? `Started a discussion in ${title}` : 'Started a discussion';
  if (normalizedType.includes('chapter')) return title ? `Created chapter ${title}` : 'Created a chapter';
  if (normalizedType.includes('study')) return title ? `Created study ${title}` : 'Created a study';
  if (normalizedType.includes('folder')) return title ? `Created folder ${title}` : 'Created a folder';
  if (normalizedType.includes('profile')) return 'Updated profile';
  return title || 'Activity';
}

function extractActivityItems(data: unknown): Record<string, unknown>[] {
  if (Array.isArray(data)) return data.filter((item): item is Record<string, unknown> => Boolean(item && typeof item === 'object'));
  if (data && typeof data === 'object') {
    const value = data as Record<string, unknown>;
    const items = value.items ?? value.activities ?? value.events ?? value.data;
    if (Array.isArray(items)) {
      return items.filter((item): item is Record<string, unknown> => Boolean(item && typeof item === 'object'));
    }
  }
  return [];
}

export async function fetchPublicActivities(username: string): Promise<PublicActivity[]> {
  const endpoints = [
    `/api/user/${encodeURIComponent(username)}/activity?limit=12`,
    `/user/${encodeURIComponent(username)}/activity?limit=12`,
    `/user/profile/${encodeURIComponent(username)}/activity?limit=12`,
  ];

  for (const endpoint of endpoints) {
    try {
      const data = await api.get(endpoint);
      return extractActivityItems(data).map(normalizeActivity).slice(0, 12);
    } catch {
      // Try the next known backend shape.
    }
  }

  return [];
}

/** 获取当前登录用户自己的资料（编辑页用）*/
export async function fetchMyProfile(): Promise<EditableProfile> {
  const data = await api.get('/user/profile');
  return {
    username: data.username ?? '',
    fide_title: data.fide_title ?? null,
    fide_rating: data.fide_rating ? Number(data.fide_rating) : null,
    cfc_rating: data.cfc_rating ? Number(data.cfc_rating) : null,
    ecf_rating: data.ecf_rating ? Number(data.ecf_rating) : null,
    chinese_athlete_title: data.chinese_athlete_title ?? null,
    lichess_username: data.lichess_username ?? null,
    chesscom_username: data.chesscom_username ?? null,
    self_intro: data.self_intro ?? null,
  };
}

/** 保存当前用户资料 */
export async function saveMyProfile(profile: EditableProfile): Promise<void> {
  await api.put('/user/profile', {
    ...profile,
    fide_rating: profile.fide_rating || null,
    cfc_rating: profile.cfc_rating || null,
    ecf_rating: profile.ecf_rating || null,
  });
}
