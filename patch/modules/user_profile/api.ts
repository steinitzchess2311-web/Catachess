// ============================================================
// user_profile — API 封装
// ============================================================

import { api } from '@ui/assets/api';
import type { EditableProfile, PublicProfile } from './types';

/**
 * 获取指定用户的公开资料
 * 后端接口：GET /user/profile/{username}（见 need_backend.md #4）
 * 当前后端还没有这个接口，先用 /user/profile 做降级处理
 */
export async function fetchPublicProfile(username: string): Promise<PublicProfile> {
  // 后端实现 GET /user/profile/{username} 后直接生效
  // 接口不存在时降级：返回只有 username 的最小资料，不触发 404
  try {
    const data = await api.get(`/user/profile/${username}`);
    return {
      username: data.username ?? username,
      fide_title: data.fide_title ?? null,
      fide_rating: data.fide_rating ? Number(data.fide_rating) : null,
      cfc_rating: data.cfc_rating ? Number(data.cfc_rating) : null,
      ecf_rating: data.ecf_rating ? Number(data.ecf_rating) : null,
      chinese_athlete_title: data.chinese_athlete_title ?? null,
      lichess_username: data.lichess_username ?? null,
      chesscom_username: data.chesscom_username ?? null,
      self_intro: data.self_intro ?? null,
    };
  } catch {
    // 后端还没有公开 profile 接口时，返回最小可用资料
    // 真正的 404（用户不存在）等后端接口就绪后才能区分
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
