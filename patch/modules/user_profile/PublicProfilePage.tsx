// ============================================================
// PublicProfilePage — /@username 公开资料展示页
//
// 所有人可见（无需登录）
// 布局：深色 Hero + 资料卡 + 最近对局
// ============================================================

import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { fetchPublicProfile } from './api';
import { useGameHistory } from '@patch/modules/user_games/hooks/useGameHistory';
import { HistoryList } from '@patch/modules/user_games/components/HistoryList';
import type { PublicProfile } from './types';
import './user_profile.css';

// ---- 称号徽章 -----------------------------------------------

function TitleBadge({ title }: { title: string }) {
  return <span className="up-title-badge">{title}</span>;
}

// ---- 评级块 -------------------------------------------------

function RatingBlock({ label, value }: { label: string; value: number | null }) {
  if (!value) return null;
  return (
    <div className="up-rating-block">
      <span className="up-rating-block__value">{value}</span>
      <span className="up-rating-block__label">{label}</span>
    </div>
  );
}

// ---- 外部链接按钮 -------------------------------------------

function ExternalLink({ href, label, icon }: { href: string; label: string; icon: string }) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="up-ext-link"
    >
      <span className="up-ext-link__icon">{icon}</span>
      <span>{label}</span>
    </a>
  );
}

// ---- 加载骨架 -----------------------------------------------

function ProfileSkeleton() {
  return (
    <div className="up-page">
      <div className="up-hero up-hero--skeleton">
        <div className="up-hero__inner">
          <div className="up-skeleton up-skeleton--avatar" />
          <div className="up-skeleton up-skeleton--title" />
          <div className="up-skeleton up-skeleton--line" />
        </div>
      </div>
    </div>
  );
}

// ---- 404 -----------------------------------------------

function NotFoundScreen({ username }: { username: string }) {
  const navigate = useNavigate();
  return (
    <div className="up-page up-page--center">
      <div className="up-notfound">
        <div className="up-notfound__piece">♟</div>
        <h2 className="up-notfound__title">User not found</h2>
        <p className="up-notfound__sub">@{username} doesn't exist on Catachess.</p>
        <button
          type="button"
          className="up-notfound__btn"
          onClick={() => navigate('/')}
        >
          Go home
        </button>
      </div>
    </div>
  );
}

// ---- 主页面 -----------------------------------------------

interface PublicProfilePageProps {
  /** 当前登录用户名，用于判断是否展示 Edit 按钮 */
  currentUsername: string | null;
}

export function PublicProfilePage({ currentUsername }: PublicProfilePageProps) {
  const { username } = useParams<{ username: string }>();
  const navigate = useNavigate();
  const cleanUsername = username?.replace(/^@/, '') ?? '';

  const [profile, setProfile] = useState<PublicProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  // 对局历史
  const { games, isLoading: gamesLoading, hasMore, error: gamesError, loadMore } =
    useGameHistory(cleanUsername);

  useEffect(() => {
    if (!cleanUsername) return;
    setLoading(true);
    setNotFound(false);
    fetchPublicProfile(cleanUsername)
      .then((data) => {
        setProfile(data);
        setNotFound(false);
      })
      .catch(() => setNotFound(true))
      .finally(() => setLoading(false));
  }, [cleanUsername]);

  const isOwnProfile = currentUsername === cleanUsername;

  if (loading) return <ProfileSkeleton />;
  if (notFound) return <NotFoundScreen username={cleanUsername} />;
  if (!profile) return null;

  const hasRatings = profile.fide_rating || profile.cfc_rating || profile.ecf_rating;
  const hasLinks = profile.lichess_username || profile.chesscom_username;

  return (
    <div className="up-page">

      {/* ── Hero 区 ── */}
      <div className="up-hero">
        {/* 棋盘格背景装饰 */}
        <div className="up-hero__chessboard" aria-hidden>
          {Array.from({ length: 64 }).map((_, i) => (
            <div
              key={i}
              className={`up-hero__sq ${(Math.floor(i / 8) + i) % 2 === 0 ? 'up-hero__sq--light' : ''}`}
            />
          ))}
        </div>

        <div className="up-hero__inner">
          {/* 头像 */}
          <div
            className="up-hero__avatar"
            style={{ background: avatarGradient(cleanUsername) }}
            aria-hidden
          >
            {cleanUsername.charAt(0).toUpperCase()}
          </div>

          {/* 称号 + 用户名 */}
          <div className="up-hero__identity">
            {profile.fide_title && <TitleBadge title={profile.fide_title} />}
            {profile.chinese_athlete_title && (
              <TitleBadge title={profile.chinese_athlete_title} />
            )}
            <h1 className="up-hero__username">{cleanUsername}</h1>
          </div>

          {/* 评级 */}
          {hasRatings && (
            <div className="up-hero__ratings">
              <RatingBlock label="FIDE" value={profile.fide_rating} />
              <RatingBlock label="CFC"  value={profile.cfc_rating}  />
              <RatingBlock label="ECF"  value={profile.ecf_rating}  />
            </div>
          )}

          {/* 编辑按钮（仅自己看到）*/}
          {isOwnProfile && (
            <button
              type="button"
              className="up-hero__edit-btn"
              onClick={() => navigate('/settings')}
            >
              Edit Profile
            </button>
          )}
        </div>
      </div>

      {/* ── 内容区 ── */}
      <div className="up-body">
        <div className="up-body__inner">

          {/* 左栏：简介 + 外部链接 */}
          <aside className="up-sidebar">

            {/* 简介 */}
            {profile.self_intro && (
              <div className="up-card">
                <h3 className="up-card__title">About</h3>
                <p className="up-card__bio">{profile.self_intro}</p>
              </div>
            )}

            {/* 外部账号 */}
            {hasLinks && (
              <div className="up-card">
                <h3 className="up-card__title">Platforms</h3>
                <div className="up-ext-links">
                  {profile.lichess_username && (
                    <ExternalLink
                      href={`https://lichess.org/@/${profile.lichess_username}`}
                      label={profile.lichess_username}
                      icon="♞"
                    />
                  )}
                  {profile.chesscom_username && (
                    <ExternalLink
                      href={`https://chess.com/member/${profile.chesscom_username}`}
                      label={profile.chesscom_username}
                      icon="♛"
                    />
                  )}
                </div>
              </div>
            )}

            {/* 评级详情卡（仅有数据时显示）*/}
            {hasRatings && (
              <div className="up-card">
                <h3 className="up-card__title">Ratings</h3>
                <div className="up-ratings-table">
                  {profile.fide_rating && (
                    <div className="up-ratings-row">
                      <span className="up-ratings-row__org">FIDE</span>
                      <span className="up-ratings-row__val">{profile.fide_rating}</span>
                    </div>
                  )}
                  {profile.cfc_rating && (
                    <div className="up-ratings-row">
                      <span className="up-ratings-row__org">CFC</span>
                      <span className="up-ratings-row__val">{profile.cfc_rating}</span>
                    </div>
                  )}
                  {profile.ecf_rating && (
                    <div className="up-ratings-row">
                      <span className="up-ratings-row__org">ECF</span>
                      <span className="up-ratings-row__val">{profile.ecf_rating}</span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </aside>

          {/* 右栏：对局历史 */}
          <main className="up-main">
            <div className="up-section-header">
              <h2 className="up-section-title">Recent Games</h2>
            </div>
            <HistoryList
              games={games}
              isLoading={gamesLoading}
              hasMore={hasMore}
              error={gamesError}
              onLoadMore={loadMore}
            />
          </main>

        </div>
      </div>
    </div>
  );
}

// ---- 工具函数 -----------------------------------------------

/** 根据用户名生成确定性渐变色 */
function avatarGradient(name: string): string {
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  const h1 = Math.abs(hash) % 360;
  const h2 = (h1 + 40) % 360;
  return `linear-gradient(135deg, hsl(${h1},50%,38%) 0%, hsl(${h2},55%,28%) 100%)`;
}
