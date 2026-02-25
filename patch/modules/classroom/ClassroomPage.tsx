// ─── /classroom ── My classrooms list ────────────────────────────────────────

import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { listClassrooms } from './api';
import type { Classroom } from './types';
import { RoleBadge } from './components/RoleBadge';
import { CreateClassroomModal } from './components/CreateClassroomModal';
import { JoinClassroomModal } from './components/JoinClassroomModal';
import './classroom.css';

// ─── Classroom card ───────────────────────────────────────────────────────────

const ClassroomCard: React.FC<{ classroom: Classroom }> = ({ classroom }) => (
  <Link to={`/classroom/${classroom.id}`} state={{ classroom }} className="cl-card">
    <div className="cl-card__accent" />
    <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 8, marginTop: 4 }}>
      <span className="cl-card__name">{classroom.name}</span>
      {classroom.archived_at && <span className="cl-card__archived">Archived</span>}
    </div>
    <div className="cl-card__meta">
      <span className="cl-card__members">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
          <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/>
          <path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75"/>
        </svg>
        {classroom.member_count} member{classroom.member_count !== 1 ? 's' : ''}
      </span>
      <RoleBadge role={classroom.my_role} />
    </div>
    <div style={{ fontSize: '0.76rem', color: 'var(--cl-text-muted)', marginTop: 2 }}>
      Since {new Date(classroom.created_at).toLocaleDateString(undefined, { month: 'short', year: 'numeric' })}
    </div>
  </Link>
);

// ─── Skeleton card ────────────────────────────────────────────────────────────

const SkeletonCard = () => (
  <div className="cl-card" style={{ cursor: 'default', pointerEvents: 'none' }}>
    <div className="cl-skeleton" style={{ height: 20, width: '65%', borderRadius: 6 }} />
    <div className="cl-skeleton" style={{ height: 14, width: '40%', borderRadius: 6, marginTop: 4 }} />
  </div>
);

// ─── Page ─────────────────────────────────────────────────────────────────────

export const ClassroomPage: React.FC = () => {
  const [classrooms, setClassrooms] = useState<Classroom[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [showJoin, setShowJoin] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    listClassrooms()
      .then(setClassrooms)
      .catch(err => setError(err?.message || 'Failed to load classrooms.'))
      .finally(() => setLoading(false));
  }, []);

  const teaching = classrooms.filter(c => c.my_role === 'owner' || c.my_role === 'teacher');
  const enrolled = classrooms.filter(c => c.my_role === 'student');

  return (
    <div className="cl-root cl-page">
      <div className="cl-page-inner">

        {/* Page header */}
        <div className="cl-page-header">
          <div>
            <h1 className="cl-page-title">Classroom</h1>
            <p className="cl-page-subtitle">Manage classes, publish tasks, and track student progress.</p>
          </div>
          <div className="cl-header-actions">
            <button className="cl-btn cl-btn-secondary" onClick={() => setShowJoin(true)}>
              Join Class
            </button>
            <button className="cl-btn cl-btn-primary" onClick={() => setShowCreate(true)}>
              + New Class
            </button>
          </div>
        </div>

        {/* Error */}
        {error && <div className="cl-error-banner" style={{ marginBottom: '1rem' }}>{error}</div>}

        {/* Loading state */}
        {loading ? (
          <div>
            <p className="cl-section-label">Teaching</p>
            <div className="cl-grid">
              <SkeletonCard /><SkeletonCard />
            </div>
          </div>
        ) : classrooms.length === 0 ? (
          <div className="cl-empty" style={{ marginTop: '3rem' }}>
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.4">
              <path d="M2 3h6a4 4 0 014 4v14a3 3 0 00-3-3H2z"/><path d="M22 3h-6a4 4 0 00-4 4v14a3 3 0 013-3h7z"/>
            </svg>
            <p className="cl-empty__title">No classrooms yet</p>
            <p className="cl-empty__sub">Create your first classroom or join one with an invite code.</p>
            <div style={{ display: 'flex', gap: '0.6rem', marginTop: '0.5rem' }}>
              <button className="cl-btn cl-btn-primary" onClick={() => setShowCreate(true)}>+ New Class</button>
              <button className="cl-btn cl-btn-secondary" onClick={() => setShowJoin(true)}>Join Class</button>
            </div>
          </div>
        ) : (
          <>
            {/* Teaching */}
            {teaching.length > 0 && (
              <section style={{ marginBottom: '2rem' }}>
                <p className="cl-section-label">Teaching ({teaching.length})</p>
                <div className="cl-grid">
                  {teaching.map(c => <ClassroomCard key={c.id} classroom={c} />)}
                </div>
              </section>
            )}

            {/* Enrolled */}
            {enrolled.length > 0 && (
              <section style={{ marginBottom: '2rem' }}>
                <p className="cl-section-label">Enrolled ({enrolled.length})</p>
                <div className="cl-grid">
                  {enrolled.map(c => <ClassroomCard key={c.id} classroom={c} />)}
                </div>
              </section>
            )}
          </>
        )}

        {/* Join banner */}
        {!loading && classrooms.length > 0 && (
          <div className="cl-join-banner">
            <span className="cl-join-banner__label">Have an invite code?</span>
            <div className="cl-join-banner__inputs">
              <InlineJoin onJoined={id => navigate(`/classroom/${id}`)} />
            </div>
          </div>
        )}

      </div>

      {showCreate && (
        <CreateClassroomModal
          onClose={() => setShowCreate(false)}
          onCreated={c => {
            setClassrooms(prev => [c, ...prev]);
            setShowCreate(false);
          }}
        />
      )}

      {showJoin && (
        <JoinClassroomModal onClose={() => setShowJoin(false)} />
      )}
    </div>
  );
};

// ─── Inline join input (in the banner) ───────────────────────────────────────

const InlineJoin: React.FC<{ onJoined: (id: string) => void }> = ({ onJoined }) => {
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handle() {
    const trimmed = code.trim().toUpperCase();
    if (!trimmed) return;
    const { joinClassroom } = await import('./api');
    setLoading(true);
    setError('');
    try {
      const res = await joinClassroom(trimmed);
      onJoined(res.classroom_id);
    } catch (err: any) {
      setError(err?.message || 'Invalid or expired code.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <input
        className="cl-join-banner__input"
        placeholder="ABC123"
        value={code}
        onChange={e => setCode(e.target.value.toUpperCase())}
        maxLength={16}
        onKeyDown={e => e.key === 'Enter' && handle()}
        style={{ flex: 1 }}
      />
      <button
        className="cl-btn cl-btn-primary cl-btn-sm"
        onClick={handle}
        disabled={loading || !code.trim()}
        style={{ flexShrink: 0 }}
      >
        {loading ? 'Joining…' : 'Join'}
      </button>
      {error && <span style={{ fontSize: '0.78rem', color: 'var(--cl-overdue)', alignSelf: 'center' }}>{error}</span>}
    </>
  );
};

