// ============================================================
// GameLobby — 创建新对局
//
// 两种模式：
//   "vs Friend"  — 指定对手 ID，双方直接进入
//   "Open Game"  — 生成可分享链接，任何人均可通过链接加入
// ============================================================

import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { GameApiError, abortGame, createGame, createOpenGame, getGameDetail } from '../api';
import type { TimeControl } from '../types';

// ---- 时间控制预设 -------------------------------------------

const TIME_PRESETS: Array<{ label: string; short: string; tc: TimeControl }> = [
  { label: 'Bullet',    short: '1+0',   tc: { initial: 60,  increment: 0 } },
  { label: 'Bullet',    short: '2+1',   tc: { initial: 120, increment: 1 } },
  { label: 'Blitz',     short: '3+0',   tc: { initial: 180, increment: 0 } },
  { label: 'Blitz',     short: '3+2',   tc: { initial: 180, increment: 2 } },
  { label: 'Blitz',     short: '5+0',   tc: { initial: 300, increment: 0 } },
  { label: 'Blitz',     short: '5+3',   tc: { initial: 300, increment: 3 } },
  { label: 'Rapid',     short: '10+0',  tc: { initial: 600, increment: 0 } },
  { label: 'Rapid',     short: '10+5',  tc: { initial: 600, increment: 5 } },
  { label: 'Classical', short: '15+10', tc: { initial: 900, increment: 10 } },
];

// ---- Props --------------------------------------------------

interface GameLobbyProps {
  myId: string;
  /** 创建成功并可进入对局后的回调 */
  onGameCreated: (gameId: string) => void;
}

// ---- 子组件：时间控制 + 颜色偏好（两个模式共用）------------

interface TcColorPickerProps {
  selectedTc: TimeControl;
  onSelectTc: (tc: TimeControl) => void;
  colorPref?: 'white' | 'black' | 'random';
  onSelectColor?: (c: 'white' | 'black' | 'random') => void;
  showColor: boolean;
}

function TcColorPicker({ selectedTc, onSelectTc, colorPref, onSelectColor, showColor }: TcColorPickerProps) {
  return (
    <>
      <div className="ug-lobby__field">
        <label className="ug-lobby__label">Time Control</label>
        <div className="ug-lobby__tc-grid">
          {TIME_PRESETS.map((p) => {
            const active =
              p.tc.initial === selectedTc.initial &&
              p.tc.increment === selectedTc.increment;
            return (
              <button
                key={`${p.tc.initial}-${p.tc.increment}`}
                type="button"
                className={`ug-lobby__tc-btn ${active ? 'ug-lobby__tc-btn--active' : ''}`}
                onClick={() => onSelectTc(p.tc)}
              >
                <span className="ug-lobby__tc-time">{p.short}</span>
                <span className="ug-lobby__tc-cat">{p.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {showColor && colorPref !== undefined && onSelectColor && (
        <div className="ug-lobby__field">
          <label className="ug-lobby__label">Play as</label>
          <div className="ug-lobby__color-row">
            {(['white', 'random', 'black'] as const).map((c) => (
              <button
                key={c}
                type="button"
                className={`ug-lobby__color-btn ${colorPref === c ? 'ug-lobby__color-btn--active' : ''}`}
                onClick={() => onSelectColor(c)}
                aria-label={c}
              >
                <span className="ug-lobby__color-icon">
                  {c === 'white' ? '♔' : c === 'black' ? '♚' : '⚖'}
                </span>
                <span>{c.charAt(0).toUpperCase() + c.slice(1)}</span>
              </button>
            ))}
          </div>
        </div>
      )}
    </>
  );
}

// ---- 主组件 -------------------------------------------------

type LobbyMode = 'friend' | 'open';

/** open game 内部阶段 */
type OpenPhase = 'idle' | 'creating' | 'waiting' | 'expired';

const OPEN_GAME_TIMEOUT_SEC = 600; // 10 分钟

export function GameLobby({ myId, onGameCreated }: GameLobbyProps) {
  // ---- 模式切换 -----------------------------------------------
  const [mode, setMode] = useState<LobbyMode>('friend');

  const navigate = useNavigate();

  // ---- vs Friend state ----------------------------------------
  const [opponentId, setOpponentId] = useState('');
  const [colorPref, setColorPref] = useState<'white' | 'black' | 'random'>('random');
  const [friendTc, setFriendTc] = useState<TimeControl>({ initial: 300, increment: 3 });
  const [friendLoading, setFriendLoading] = useState(false);
  const [friendError, setFriendError] = useState<string | null>(null);
  const [friendBlockedGameId, setFriendBlockedGameId] = useState<string | null>(null);

  // ---- Open Game state ----------------------------------------
  const [openTc, setOpenTc] = useState<TimeControl>({ initial: 300, increment: 3 });
  const [openPhase, setOpenPhase] = useState<OpenPhase>('idle');
  const [openGameId, setOpenGameId] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [countdown, setCountdown] = useState(OPEN_GAME_TIMEOUT_SEC);
  const [openError, setOpenError] = useState<string | null>(null);
  const [openBlockedGameId, setOpenBlockedGameId] = useState<string | null>(null);

  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const countdownRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // ---- vs Friend: 提交 ----------------------------------------
  const handleFriendSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const opponent = opponentId.trim();
    if (!opponent) return;
    if (opponent === myId) {
      setFriendError("You can't play against yourself.");
      return;
    }
    setFriendLoading(true);
    setFriendError(null);
    setFriendBlockedGameId(null);
    try {
      const game = await createGame(myId, opponent, friendTc, colorPref);
      onGameCreated(game.game_id);
    } catch (err) {
      if (err instanceof GameApiError && err.code === 'user_already_in_game') {
        setFriendError('You are already in an active game.');
        setFriendBlockedGameId(err.currentGameId ?? null);
      } else {
        setFriendError(err instanceof Error ? err.message : 'Failed to create game.');
      }
      setFriendLoading(false);
    }
  };

  // ---- Open Game: 创建 ----------------------------------------
  const handleCreateOpen = async () => {
    setOpenPhase('creating');
    setOpenError(null);
    setOpenBlockedGameId(null);
    try {
      const res = await createOpenGame(myId, openTc);
      setOpenGameId(res.game_id);
      setCountdown(OPEN_GAME_TIMEOUT_SEC);
      setOpenPhase('waiting');
    } catch (err) {
      if (err instanceof GameApiError && err.code === 'user_already_in_game') {
        setOpenError('You are already in an active game.');
        setOpenBlockedGameId(err.currentGameId ?? null);
      } else {
        setOpenError(err instanceof Error ? err.message : 'Failed to create game link.');
      }
      setOpenPhase('idle');
    }
  };

  // ---- Open Game: 轮询对手是否加入 ---------------------------
  useEffect(() => {
    if (openPhase !== 'waiting' || !openGameId) return;

    pollRef.current = setInterval(async () => {
      try {
        const game = await getGameDetail(openGameId);
        if (game.status === 'waiting' || game.status === 'ongoing') {
          clearInterval(pollRef.current!);
          clearInterval(countdownRef.current!);
          onGameCreated(openGameId);
        } else if (game.status === 'aborted' || game.status === 'completed') {
          clearInterval(pollRef.current!);
          clearInterval(countdownRef.current!);
          setOpenPhase('expired');
        }
      } catch { /* network blip, ignore */ }
    }, 2000);

    return () => clearInterval(pollRef.current!);
  }, [openPhase, openGameId, onGameCreated]);

  // ---- Open Game: 倒计时 -------------------------------------
  useEffect(() => {
    if (openPhase !== 'waiting') return;

    countdownRef.current = setInterval(() => {
      setCountdown((n) => {
        if (n <= 1) {
          clearInterval(countdownRef.current!);
          clearInterval(pollRef.current!);
          setOpenPhase('expired');
          return 0;
        }
        return n - 1;
      });
    }, 1000);

    return () => clearInterval(countdownRef.current!);
  }, [openPhase]);

  // ---- Open Game: 取消/中止 ----------------------------------
  const handleCancelOpen = useCallback(async () => {
    clearInterval(pollRef.current!);
    clearInterval(countdownRef.current!);
    if (openGameId) {
      try { await abortGame(openGameId, myId); } catch { /* ignore */ }
    }
    setOpenPhase('idle');
    setOpenGameId(null);
    setCopied(false);
  }, [openGameId, myId]);

  // ---- 复制链接 -----------------------------------------------
  const shareUrl = openGameId
    ? `${window.location.origin}/games/${openGameId}/join`
    : '';

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(shareUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // 回退：选择文本
    }
  };

  // ---- 倒计时格式化 -------------------------------------------
  const mins = String(Math.floor(countdown / 60)).padStart(2, '0');
  const secs = String(countdown % 60).padStart(2, '0');
  const countdownStr = `${mins}:${secs}`;
  const isUrgent = countdown <= 60;

  // ---- 切换模式时重置 ----------------------------------------
  const switchMode = (m: LobbyMode) => {
    if (m === mode) return;
    setMode(m);
    setFriendError(null);
    setOpenError(null);
  };

  // ================================================================
  // Render
  // ================================================================

  return (
    <div className="ug-lobby">
      <h2 className="ug-lobby__title">New Game</h2>

      {/* 模式选项卡 */}
      <div className="ug-lobby__tabs" role="tablist">
        <button
          role="tab"
          type="button"
          aria-selected={mode === 'friend'}
          className={`ug-lobby__tab ${mode === 'friend' ? 'ug-lobby__tab--active' : ''}`}
          onClick={() => switchMode('friend')}
        >
          vs Friend
        </button>
        <button
          role="tab"
          type="button"
          aria-selected={mode === 'open'}
          className={`ug-lobby__tab ${mode === 'open' ? 'ug-lobby__tab--active' : ''}`}
          onClick={() => switchMode('open')}
        >
          Share Link
        </button>
      </div>

      {/* ---- vs Friend ---- */}
      {mode === 'friend' && (
        <form className="ug-lobby__form" onSubmit={handleFriendSubmit}>
          <div className="ug-lobby__field">
            <label className="ug-lobby__label" htmlFor="opponent-id">
              Opponent username
            </label>
            <input
              id="opponent-id"
              type="text"
              className="ug-lobby__input"
              placeholder="Enter username"
              value={opponentId}
              onChange={(e) => setOpponentId(e.target.value)}
              autoComplete="off"
              autoFocus
              disabled={friendLoading}
            />
          </div>

          <TcColorPicker
            selectedTc={friendTc}
            onSelectTc={setFriendTc}
            colorPref={colorPref}
            onSelectColor={setColorPref}
            showColor
          />

          {friendError && (
            <div className="ug-lobby__error">
              {friendError}
              {friendBlockedGameId && (
                <button
                  type="button"
                  className="ug-lobby__goto-game"
                  onClick={() => navigate(`/games/${friendBlockedGameId}`)}
                >
                  Go to your game →
                </button>
              )}
            </div>
          )}

          <button
            type="submit"
            className="ug-lobby__submit"
            disabled={friendLoading || !opponentId.trim()}
          >
            {friendLoading ? 'Creating…' : 'Challenge'}
          </button>
        </form>
      )}

      {/* ---- Open Game ---- */}
      {mode === 'open' && (
        <div className="ug-lobby__form">
          {/* idle — 选时间控制，生成链接 */}
          {openPhase === 'idle' && (
            <>
              <p className="ug-lobby__open-hint">
                Generate a link and share it with anyone — they can join without an account.
                The server randomly assigns colors.
              </p>
              <TcColorPicker
                selectedTc={openTc}
                onSelectTc={setOpenTc}
                showColor={false}
              />
              {openError && (
                <div className="ug-lobby__error">
                  {openError}
                  {openBlockedGameId && (
                    <button
                      type="button"
                      className="ug-lobby__goto-game"
                      onClick={() => navigate(`/games/${openBlockedGameId}`)}
                    >
                      Go to your game →
                    </button>
                  )}
                </div>
              )}
              <button
                type="button"
                className="ug-lobby__submit"
                onClick={handleCreateOpen}
              >
                Create Link
              </button>
            </>
          )}

          {/* creating — 旋转中 */}
          {openPhase === 'creating' && (
            <div className="ug-lobby__open-spinner-wrap">
              <div className="ug-lobby__spinner" />
              <span>Generating link…</span>
            </div>
          )}

          {/* waiting — 等待对手 */}
          {openPhase === 'waiting' && (
            <div className="ug-lobby__open-waiting">
              <p className="ug-lobby__open-waiting__label">Share this link</p>

              <div className="ug-lobby__link-row">
                <input
                  className="ug-lobby__link-input"
                  readOnly
                  value={shareUrl}
                  onFocus={(e) => e.target.select()}
                />
                <button
                  type="button"
                  className={`ug-lobby__link-copy ${copied ? 'ug-lobby__link-copy--copied' : ''}`}
                  onClick={handleCopy}
                  title="Copy link"
                >
                  {copied ? '✓ Copied' : 'Copy'}
                </button>
              </div>

              <div className="ug-lobby__open-status">
                <div className="ug-lobby__spinner ug-lobby__spinner--sm" />
                <span>Waiting for opponent…</span>
              </div>

              <div className={`ug-lobby__open-countdown ${isUrgent ? 'ug-lobby__open-countdown--urgent' : ''}`}>
                Link expires in <strong>{countdownStr}</strong>
              </div>

              <button
                type="button"
                className="ug-lobby__cancel"
                onClick={handleCancelOpen}
              >
                Cancel
              </button>
            </div>
          )}

          {/* expired */}
          {openPhase === 'expired' && (
            <div className="ug-lobby__open-expired">
              <span className="ug-lobby__open-expired__icon">⏱</span>
              <p>The link expired before anyone joined.</p>
              <button
                type="button"
                className="ug-lobby__submit"
                onClick={() => { setOpenPhase('idle'); setOpenGameId(null); }}
              >
                Create New Link
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
