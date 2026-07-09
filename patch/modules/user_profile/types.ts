// ============================================================
// user_profile — 类型定义
// Created at: 2026-07-08 21:07 EDT
// Created by: Codex
// Last Modified at: 2026-07-08 22:04 EDT
// Last Modified by: Codex
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
  total_online_seconds: number;
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

/** 中国棋协称号列表（公开页只显示短称号） */
export const CHINESE_CHESS_ASSOCIATION_TITLES = ['三运', '二运', '一运', '候补', '棋协'] as const;

export type ChineseChessAssociationTitle = typeof CHINESE_CHESS_ASSOCIATION_TITLES[number];

const CHINESE_TITLE_ALIASES: Record<string, ChineseChessAssociationTitle> = {
  '三运': '三运',
  '三级运动员': '三运',
  '国家三级运动员': '三运',
  '二运': '二运',
  '二级运动员': '二运',
  '国家二级运动员': '二运',
  '一运': '一运',
  '一级运动员': '一运',
  '国家一级运动员': '一运',
  '候补': '候补',
  '候补棋协大师': '候补',
  '棋协': '棋协',
  '棋协大师': '棋协',
  '中国棋协大师': '棋协',
};

/** Normalize persisted legacy labels into the product's short public title set. */
export function normalizeChineseChessAssociationTitle(
  value: string | null | undefined,
): ChineseChessAssociationTitle | null {
  if (!value) return null;
  return CHINESE_TITLE_ALIASES[value.trim()] ?? null;
}

export function profileTitlePrefix(profile: PublicProfile): string | null {
  const fideTitle = profile.fide_title?.trim();
  if (fideTitle) return fideTitle;
  return normalizeChineseChessAssociationTitle(profile.chinese_athlete_title);
}
