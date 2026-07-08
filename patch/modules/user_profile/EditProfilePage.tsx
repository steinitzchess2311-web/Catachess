// ============================================================
// EditProfilePage — /settings 编辑个人资料页
//
// 仅登录用户可访问（App.tsx 里用 <Protected> 包裹）
// 保存成功后自动跳转到公开页
// ============================================================

import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import LogoutButton from '../../../frontend/web/src/components/dialogBox/LogoutButton';
import { fetchMyProfile, saveMyProfile } from './api';
import { FIDE_TITLES } from './types';
import type { EditableProfile } from './types';
import './user_profile.css';

// ---- 单个表单字段 -------------------------------------------

interface FieldProps {
  label: string;
  hint?: string;
  children: React.ReactNode;
}

function Field({ label, hint, children }: FieldProps) {
  return (
    <div className="up-edit-field">
      <label className="up-edit-label">{label}</label>
      {hint && <span className="up-edit-hint">{hint}</span>}
      {children}
    </div>
  );
}

// ---- 保存状态提示 -------------------------------------------

type SaveState = 'idle' | 'saving' | 'success' | 'error';

function SaveToast({ state, message }: { state: SaveState; message?: string }) {
  if (state === 'idle') return null;
  return (
    <div className={`up-edit-toast up-edit-toast--${state}`}>
      {state === 'saving' && 'Saving...'}
      {state === 'success' && '✓ Profile saved'}
      {state === 'error' && (message || 'Failed to save. Please try again.')}
    </div>
  );
}

// ---- 主组件 -----------------------------------------------

interface EditProfilePageProps {
  /** 当前登录用户名，用于跳转到自己的公开页 */
  currentUsername: string | null;
}

const EMPTY: EditableProfile = {
  username: '',
  fide_title: null,
  fide_rating: null,
  cfc_rating: null,
  ecf_rating: null,
  chinese_athlete_title: null,
  lichess_username: null,
  chesscom_username: null,
  self_intro: null,
};

export function EditProfilePage({ currentUsername }: EditProfilePageProps) {
  const navigate = useNavigate();
  const [profile, setProfile] = useState<EditableProfile>(EMPTY);
  const [loading, setLoading] = useState(true);
  const [saveState, setSaveState] = useState<SaveState>('idle');
  const [saveMessage, setSaveMessage] = useState('');
  const toastTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // 加载当前资料
  useEffect(() => {
    fetchMyProfile()
      .then(setProfile)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  // 字段更新辅助函数
  const set = <K extends keyof EditableProfile>(key: K, value: EditableProfile[K]) => {
    setProfile((prev) => ({ ...prev, [key]: value || null }));
  };

  const handleSave = async () => {
    setSaveState('saving');
    if (toastTimer.current) clearTimeout(toastTimer.current);

    try {
      await saveMyProfile(profile);
      setSaveState('success');
      // 3 秒后消失，然后跳到公开页
      toastTimer.current = setTimeout(() => {
        setSaveState('idle');
        if (currentUsername) navigate(`/@${currentUsername}`);
      }, 1800);
    } catch (e) {
      setSaveState('error');
      setSaveMessage(e instanceof Error ? e.message : 'Unknown error');
      toastTimer.current = setTimeout(() => setSaveState('idle'), 4000);
    }
  };

  if (loading) {
    return (
      <div className="up-page up-page--center">
        <div className="explorer-loading">
          <div className="explorer-loading__dot" />
          <div className="explorer-loading__dot" />
          <div className="explorer-loading__dot" />
        </div>
      </div>
    );
  }

  return (
    <div className="up-page up-edit-page">

      {/* 页头 */}
      <div className="up-edit-header">
        <div className="up-edit-header__inner">
          <button
            type="button"
            className="up-edit-back-btn"
            onClick={() => currentUsername ? navigate(`/@${currentUsername}`) : navigate('/')}
            aria-label="Back to profile"
          >
            ← Back
          </button>
          <div>
            <h1 className="up-edit-title">Edit Profile</h1>
            <p className="up-edit-subtitle">
              Your public profile is visible to everyone on Catachess.
            </p>
          </div>
          <button
            type="button"
            className="up-edit-save-btn"
            onClick={handleSave}
            disabled={saveState === 'saving'}
          >
            {saveState === 'saving' ? 'Saving...' : 'Save Changes'}
          </button>
          <LogoutButton />
        </div>
      </div>

      {/* 表单区 */}
      <div className="up-edit-body">
        <div className="up-edit-body__inner">

          {/* ── 第一列：棋棋身份 ── */}
          <section className="up-edit-section">
            <h2 className="up-edit-section-title">Chess Identity</h2>

            <Field label="FIDE Title">
              <div className="up-edit-title-grid">
                {/* 空选（无称号）*/}
                <button
                  type="button"
                  className={`up-edit-title-btn ${!profile.fide_title ? 'up-edit-title-btn--active' : ''}`}
                  onClick={() => set('fide_title', null)}
                >
                  None
                </button>
                {FIDE_TITLES.map((t) => (
                  <button
                    key={t}
                    type="button"
                    className={`up-edit-title-btn ${profile.fide_title === t ? 'up-edit-title-btn--active' : ''}`}
                    onClick={() => set('fide_title', t)}
                  >
                    {t}
                  </button>
                ))}
              </div>
            </Field>

            <Field label="Chinese Athlete Title" hint="e.g. 国际级运动健将">
              <input
                className="up-edit-input"
                type="text"
                value={profile.chinese_athlete_title ?? ''}
                onChange={(e) => set('chinese_athlete_title', e.target.value)}
                placeholder="e.g. 国际级运动健将"
              />
            </Field>

            <div className="up-edit-ratings-grid">
              <Field label="FIDE Rating">
                <input
                  className="up-edit-input"
                  type="number"
                  value={profile.fide_rating ?? ''}
                  onChange={(e) => set('fide_rating', e.target.value ? Number(e.target.value) : null)}
                  placeholder="e.g. 2350"
                  min={0}
                  max={3300}
                />
              </Field>
              <Field label="CFC Rating">
                <input
                  className="up-edit-input"
                  type="number"
                  value={profile.cfc_rating ?? ''}
                  onChange={(e) => set('cfc_rating', e.target.value ? Number(e.target.value) : null)}
                  placeholder="e.g. 2100"
                  min={0}
                  max={3300}
                />
              </Field>
              <Field label="ECF Rating">
                <input
                  className="up-edit-input"
                  type="number"
                  value={profile.ecf_rating ?? ''}
                  onChange={(e) => set('ecf_rating', e.target.value ? Number(e.target.value) : null)}
                  placeholder="e.g. 190"
                  min={0}
                  max={3300}
                />
              </Field>
            </div>
          </section>

          {/* ── 第二列：平台账号 + 简介 ── */}
          <section className="up-edit-section">
            <h2 className="up-edit-section-title">Platforms & Bio</h2>

            <Field label="Lichess Username">
              <div className="up-edit-input-wrap">
                <span className="up-edit-input-prefix">lichess.org/@/</span>
                <input
                  className="up-edit-input up-edit-input--with-prefix"
                  type="text"
                  value={profile.lichess_username ?? ''}
                  onChange={(e) => set('lichess_username', e.target.value)}
                  placeholder="your-lichess-name"
                />
              </div>
            </Field>

            <Field label="Chess.com Username">
              <div className="up-edit-input-wrap">
                <span className="up-edit-input-prefix">chess.com/member/</span>
                <input
                  className="up-edit-input up-edit-input--with-prefix"
                  type="text"
                  value={profile.chesscom_username ?? ''}
                  onChange={(e) => set('chesscom_username', e.target.value)}
                  placeholder="your-chesscom-name"
                />
              </div>
            </Field>

            <Field label="About You" hint="A short introduction shown on your public profile">
              <textarea
                className="up-edit-textarea"
                rows={5}
                value={profile.self_intro ?? ''}
                onChange={(e) => set('self_intro', e.target.value)}
                placeholder="Tell others about yourself — your chess journey, favorite openings, etc."
                maxLength={500}
              />
              <div className="up-edit-char-count">
                {(profile.self_intro?.length ?? 0)} / 500
              </div>
            </Field>
          </section>

        </div>
      </div>

      {/* 保存状态 Toast */}
      <SaveToast state={saveState} message={saveMessage} />
    </div>
  );
}
