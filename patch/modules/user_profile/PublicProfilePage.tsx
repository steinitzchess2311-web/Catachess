// ============================================================
// PublicProfilePage — /@username public profile
// ============================================================

import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { fetchPublicActivities, fetchPublicProfile } from './api';
import type { PublicActivity, PublicProfile } from './types';
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

function formatActivityDate(value: string): { day: string; time: string } {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return { day: '', time: '' };
  }
  return {
    day: date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' }),
    time: date.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' }),
  };
}

function activityLabel(type: string): string {
  const normalized = type.toLowerCase();
  if (normalized.includes('study')) return 'Study';
  if (normalized.includes('chapter')) return 'Chapter';
  if (normalized.includes('discussion') || normalized.includes('comment')) return 'Discussion';
  if (normalized.includes('folder')) return 'Folder';
  if (normalized.includes('profile')) return 'Profile';
  if (normalized.includes('game')) return 'Game';
  return 'Activity';
}

function ActivityTimeline({
  activities,
  loading,
}: {
  activities: PublicActivity[];
  loading: boolean;
}) {
  if (loading) {
    return (
      <div className="up-activity-list" aria-busy="true">
        {[0, 1, 2].map((item) => (
          <div key={item} className="up-activity up-activity--loading">
            <span className="up-activity__date up-skeleton" />
            <span className="up-activity__marker" />
            <span className="up-activity__body">
              <span className="up-skeleton up-skeleton--activity-title" />
              <span className="up-skeleton up-skeleton--activity-line" />
            </span>
          </div>
        ))}
      </div>
    );
  }

  if (activities.length === 0) {
    return (
      <div className="up-activity-empty">
        <p>No public activity yet.</p>
      </div>
    );
  }

  return (
    <div className="up-activity-list">
      {activities.map((activity) => {
        const date = formatActivityDate(activity.occurred_at);
        return (
          <article key={activity.id} className="up-activity">
            <time className="up-activity__date" dateTime={activity.occurred_at}>
              <span>{date.day}</span>
              <small>{date.time}</small>
            </time>
            <span className="up-activity__marker" aria-hidden />
            <div className="up-activity__body">
              <div className="up-activity__topline">
                <span className="up-activity__type">{activityLabel(activity.type)}</span>
                {activity.target_url ? (
                  <a className="up-activity__target" href={activity.target_url}>
                    {activity.target_title || 'Open'}
                  </a>
                ) : activity.target_title ? (
                  <span className="up-activity__target">{activity.target_title}</span>
                ) : null}
              </div>
              <p className="up-activity__summary">{activity.summary}</p>
            </div>
          </article>
        );
      })}
    </div>
  );
}

// ---- 外部链接按钮 -------------------------------------------

function ExternalLink({ href, label, imgSrc }: { href: string; label: string; imgSrc: string }) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="up-ext-link"
    >
      <img src={imgSrc} alt={label} className="up-ext-link__img" />
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
  // 路由参数名可能是 :username（旧）或 :id（当前 /:id 路由），兼容两种
  const params = useParams<{ username?: string; id?: string }>();
  const navigate = useNavigate();
  const cleanUsername = (params.username ?? params.id ?? '').replace(/^@/, '');

  const [profile, setProfile] = useState<PublicProfile | null>(null);
  const [activities, setActivities] = useState<PublicActivity[]>([]);
  const [activitiesLoading, setActivitiesLoading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

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

  useEffect(() => {
    if (!cleanUsername) return;
    setActivitiesLoading(true);
    fetchPublicActivities(cleanUsername)
      .then(setActivities)
      .catch(() => setActivities([]))
      .finally(() => setActivitiesLoading(false));
  }, [cleanUsername]);

  const isOwnProfile = currentUsername === cleanUsername;

  if (loading) return <ProfileSkeleton />;
  if (notFound) return <NotFoundScreen username={cleanUsername} />;
  if (!profile) return null;

  const hasRatings = profile.fide_rating || profile.cfc_rating || profile.ecf_rating;
  const hasLinks = profile.lichess_username || profile.chesscom_username;
  const hasSidebar = Boolean(profile.self_intro || hasLinks || hasRatings);

  return (
    <div className="up-page">

      <div className="up-hero">
        <div className="up-hero__inner">
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

          {hasRatings && (
            <div className="up-hero__ratings">
              <RatingBlock label="FIDE" value={profile.fide_rating} />
              <RatingBlock label="CFC"  value={profile.cfc_rating}  />
              <RatingBlock label="ECF"  value={profile.ecf_rating}  />
            </div>
          )}

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

      <div className="up-body">
        <div className={`up-body__inner ${hasSidebar ? '' : 'up-body__inner--single'}`}>

          <aside className="up-sidebar">

            {profile.self_intro && (
              <div className="up-card">
                <h3 className="up-card__title">About</h3>
                <p className="up-card__bio">{profile.self_intro}</p>
              </div>
            )}

            {hasLinks && (
              <div className="up-card">
                <h3 className="up-card__title">Platforms</h3>
                <div className="up-ext-links">
                  {profile.lichess_username && (
                    <ExternalLink
                      href={`https://lichess.org/@/${profile.lichess_username}`}
                      label={profile.lichess_username}
                      imgSrc="/assets/lichess.png"
                    />
                  )}
                  {profile.chesscom_username && (
                    <ExternalLink
                      href={`https://chess.com/member/${profile.chesscom_username}`}
                      label={profile.chesscom_username}
                      imgSrc="/assets/chess-com.png"
                    />
                  )}
                </div>
              </div>
            )}

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

          <main className="up-main">
            <div className="up-section-header">
              <h2 className="up-section-title">Recent Activities</h2>
            </div>
            <ActivityTimeline activities={activities} loading={activitiesLoading} />
          </main>

        </div>
      </div>
    </div>
  );
}

// ---- 工具函数 -----------------------------------------------

/** 根据用户名生成确定性渐变色 */
function avatarGradient(name: string): string {
  const palette = [
    ['#166b5c', '#0f584b'],
    ['#4f6f52', '#36543a'],
    ['#6f6336', '#4f4727'],
    ['#3f6470', '#2f4d57'],
    ['#6b5d4f', '#4c4339'],
  ];
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  const [from, to] = palette[Math.abs(hash) % palette.length];
  return `linear-gradient(135deg, ${from} 0%, ${to} 100%)`;
}
