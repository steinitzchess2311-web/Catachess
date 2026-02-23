// ============================================================
// PlayerBar — 棋手信息栏（头像占位 + 名字 + 时钟）
// 出现在棋盘上下两端
// ============================================================

import React from 'react';
import { Clock } from './Clock';
import type { PlayerColor } from '../types';

interface PlayerBarProps {
  playerId: string;
  color: PlayerColor;
  timeMs: number;
  isActive: boolean;
  isOver?: boolean;
  isMe?: boolean;
  isDisconnected?: boolean;
}

/** 根据棋手 ID 生成一个固定的颜色，用于头像背景 */
function avatarColor(id: string): string {
  let hash = 0;
  for (let i = 0; i < id.length; i++) {
    hash = id.charCodeAt(i) + ((hash << 5) - hash);
  }
  const hue = Math.abs(hash) % 360;
  return `hsl(${hue}, 45%, 45%)`;
}

/** 取名字首字符作为头像文字 */
function avatarInitial(id: string): string {
  return id.charAt(0).toUpperCase();
}

export function PlayerBar({
  playerId,
  color,
  timeMs,
  isActive,
  isOver,
  isMe,
  isDisconnected,
}: PlayerBarProps) {
  return (
    <div className={`ug-player-bar ${isActive ? 'ug-player-bar--active' : ''}`}>
      {/* 头像 */}
      <div
        className="ug-player-bar__avatar"
        style={{ background: avatarColor(playerId) }}
        aria-hidden
      >
        {avatarInitial(playerId)}
      </div>

      {/* 名字区域 */}
      <div className="ug-player-bar__info">
        <span className="ug-player-bar__name">
          {playerId}
          {isMe && <span className="ug-player-bar__you-tag">You</span>}
        </span>
        {isDisconnected && (
          <span className="ug-player-bar__disconnected">disconnected</span>
        )}
      </div>

      {/* 棋子颜色指示 */}
      <div className={`ug-player-bar__piece-dot ug-player-bar__piece-dot--${color}`} aria-hidden />

      {/* 时钟 */}
      <Clock timeMs={timeMs} isActive={isActive} isOver={isOver} />
    </div>
  );
}
