// ============================================================
// GameLobby — 创建新对局表单
// 支持指定对手、时间控制、颜色偏好
// ============================================================

import React, { useState } from 'react';
import { createGame } from '../api';
import type { TimeControl } from '../types';

// 预设时间控制选项
const TIME_PRESETS: Array<{ label: string; tc: TimeControl }> = [
  { label: '1+0  Bullet',    tc: { initial: 60,  increment: 0 } },
  { label: '2+1  Bullet',    tc: { initial: 120, increment: 1 } },
  { label: '3+0  Blitz',     tc: { initial: 180, increment: 0 } },
  { label: '3+2  Blitz',     tc: { initial: 180, increment: 2 } },
  { label: '5+0  Blitz',     tc: { initial: 300, increment: 0 } },
  { label: '5+3  Blitz',     tc: { initial: 300, increment: 3 } },
  { label: '10+0 Rapid',     tc: { initial: 600, increment: 0 } },
  { label: '10+5 Rapid',     tc: { initial: 600, increment: 5 } },
  { label: '15+10 Classical',tc: { initial: 900, increment: 10 } },
];

interface GameLobbyProps {
  myId: string;
  /** 创建成功后返回 game_id */
  onGameCreated: (gameId: string) => void;
}

export function GameLobby({ myId, onGameCreated }: GameLobbyProps) {
  const [opponentId, setOpponentId] = useState('');
  const [selectedTc, setSelectedTc] = useState<TimeControl>({ initial: 300, increment: 3 });
  const [colorPref, setColorPref] = useState<'white' | 'black' | 'random'>('random');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const opponent = opponentId.trim();
    if (!opponent) return;
    if (opponent === myId) {
      setError("You can't play against yourself.");
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const game = await createGame(myId, opponent, selectedTc, colorPref);
      onGameCreated(game.game_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create game.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="ug-lobby">
      <h2 className="ug-lobby__title">New Game</h2>
      <p className="ug-lobby__subtitle">
        Enter your opponent's username to challenge them.
      </p>

      <form className="ug-lobby__form" onSubmit={handleSubmit}>
        {/* 对手 ID */}
        <div className="ug-lobby__field">
          <label className="ug-lobby__label" htmlFor="opponent-id">
            Opponent
          </label>
          <input
            id="opponent-id"
            type="text"
            className="ug-lobby__input"
            placeholder="Username"
            value={opponentId}
            onChange={(e) => setOpponentId(e.target.value)}
            autoComplete="off"
            autoFocus
          />
        </div>

        {/* 时间控制 */}
        <div className="ug-lobby__field">
          <label className="ug-lobby__label">Time Control</label>
          <div className="ug-lobby__tc-grid">
            {TIME_PRESETS.map((p) => {
              const active =
                p.tc.initial === selectedTc.initial &&
                p.tc.increment === selectedTc.increment;
              return (
                <button
                  key={p.label}
                  type="button"
                  className={`ug-lobby__tc-btn ${active ? 'ug-lobby__tc-btn--active' : ''}`}
                  onClick={() => setSelectedTc(p.tc)}
                >
                  {p.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* 颜色偏好 */}
        <div className="ug-lobby__field">
          <label className="ug-lobby__label">Play as</label>
          <div className="ug-lobby__color-row">
            {(['white', 'random', 'black'] as const).map((c) => (
              <button
                key={c}
                type="button"
                className={`ug-lobby__color-btn ${colorPref === c ? 'ug-lobby__color-btn--active' : ''}`}
                onClick={() => setColorPref(c)}
                aria-label={c}
              >
                {c === 'white' ? '♔' : c === 'black' ? '♚' : '⚖'}
                <span>{c.charAt(0).toUpperCase() + c.slice(1)}</span>
              </button>
            ))}
          </div>
        </div>

        {/* 错误提示 */}
        {error && <div className="ug-lobby__error">{error}</div>}

        {/* 提交 */}
        <button
          type="submit"
          className="ug-lobby__submit"
          disabled={isLoading || !opponentId.trim()}
        >
          {isLoading ? 'Creating...' : 'Challenge'}
        </button>
      </form>
    </div>
  );
}
