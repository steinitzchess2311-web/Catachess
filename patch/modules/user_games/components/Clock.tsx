// ============================================================
// Clock — 倒计时组件
//
// 本地用 requestAnimationFrame 平滑倒计时，
// 每次收到服务器 time_update 时由父组件更新 timeMs 进行校正
// ============================================================

import React, { useEffect, useRef, useState } from 'react';

interface ClockProps {
  /** 当前剩余时间（毫秒），服务器校正值 */
  timeMs: number;
  /** 是否是当前走棋方（active 时倒计时，否则暂停）*/
  isActive: boolean;
  /** 是否对局已结束（结束后冻结显示）*/
  isOver?: boolean;
}

/** 将毫秒格式化为 mm:ss 或 s.x（最后 20 秒显示小数）*/
function formatTime(ms: number): string {
  if (ms <= 0) return '0:00';
  const totalSec = ms / 1000;

  // 最后 20 秒：显示 ss.x
  if (totalSec < 20) {
    return totalSec.toFixed(1);
  }

  const mins = Math.floor(totalSec / 60);
  const secs = Math.floor(totalSec % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

export function Clock({ timeMs, isActive, isOver = false }: ClockProps) {
  // 本地维护显示值（毫秒），跟随 props 校正
  const [displayMs, setDisplayMs] = useState(timeMs);
  const displayRef = useRef(timeMs);
  const rafRef = useRef<number | null>(null);
  const lastTimestampRef = useRef<number | null>(null);
  const isActiveRef = useRef(isActive);
  isActiveRef.current = isActive;

  // 服务器校正：props.timeMs 变化时强制同步本地值
  useEffect(() => {
    displayRef.current = timeMs;
    setDisplayMs(timeMs);
  }, [timeMs]);

  // requestAnimationFrame 倒计时循环
  useEffect(() => {
    if (!isActive || isOver) {
      if (rafRef.current !== null) {
        cancelAnimationFrame(rafRef.current);
        rafRef.current = null;
      }
      lastTimestampRef.current = null;
      return;
    }

    const tick = (timestamp: number) => {
      if (!isActiveRef.current) return;

      if (lastTimestampRef.current !== null) {
        const delta = timestamp - lastTimestampRef.current;
        displayRef.current = Math.max(0, displayRef.current - delta);
        setDisplayMs(displayRef.current);
      }
      lastTimestampRef.current = timestamp;

      // 时间耗尽停止循环
      if (displayRef.current > 0) {
        rafRef.current = requestAnimationFrame(tick);
      }
    };

    rafRef.current = requestAnimationFrame(tick);

    return () => {
      if (rafRef.current !== null) {
        cancelAnimationFrame(rafRef.current);
        rafRef.current = null;
      }
      lastTimestampRef.current = null;
    };
  }, [isActive, isOver]);

  const isLow = displayMs < 20_000;    // 低于 20 秒变红
  const isDanger = displayMs < 10_000; // 低于 10 秒加速跳动动画

  return (
    <div
      className={[
        'ug-clock',
        isActive ? 'ug-clock--active' : 'ug-clock--paused',
        isLow ? 'ug-clock--low' : '',
        isDanger ? 'ug-clock--danger' : '',
        isOver ? 'ug-clock--over' : '',
      ]
        .filter(Boolean)
        .join(' ')}
      aria-label={`${formatTime(displayMs)} remaining`}
    >
      {formatTime(displayMs)}
    </div>
  );
}
