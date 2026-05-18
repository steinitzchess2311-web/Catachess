// ============================================================
// user_profile — 类型定义
// ============================================================

/** 用户公开资料（任何人可见）*/
export interface PublicProfile {
  username: string;
  fide_title: string | null;
  fide_rating: number | null;
  cfc_rating: number | null;
  ecf_rating: number | null;
  chinese_athlete_title: string | null;
  lichess_username: string | null;
  chesscom_username: string | null;
  self_intro: string | null;
}

export interface PublicActivity {
  id: string;
  type: string;
  summary: string;
  occurred_at: string;
  target_title?: string | null;
  target_url?: string | null;
}

/** 用户私人资料（编辑表单用）*/
export interface EditableProfile extends PublicProfile {
  // 目前与 PublicProfile 字段相同，后续可扩展
}

/** FIDE 称号列表 */
export const FIDE_TITLES = ['GM', 'WGM', 'IM', 'WIM', 'FM', 'WFM', 'CM', 'WCM', 'NM'] as const;
