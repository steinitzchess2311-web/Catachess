// ─── /classroom/:id ── Classroom detail ──────────────────────────────────────

import React, { useEffect, useState } from 'react';
import { Link, useParams, useNavigate, useLocation } from 'react-router-dom';
import { getClassroom, archiveClassroom, unarchiveClassroom, deleteClassroom, renameClassroom, leaveClassroom } from './api';
import type { Classroom } from './types';
import { RoleBadge } from './components/RoleBadge';
import { TeacherOverview, StudentOverview } from './components/OverviewTab';
import { MembersTab } from './components/MembersTab';
import { AssignmentsTab } from './components/AssignmentsTab';
import { BroadcastModal } from './components/BroadcastModal';
import './classroom.css';

type Tab = 'overview' | 'assignments' | 'members';

export const ClassroomDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const location = useLocation();

  // ── If we navigated from the list page, the classroom object (with my_role)
  // is already available in router state — use it immediately so role-based UI
  // renders correctly on first paint without waiting for the fetch.
  const stateClassroom = (location.state as { classroom?: Classroom } | null)?.classroom ?? null;

  const [classroom, setClassroom] = useState<Classroom | null>(stateClassroom);
  const [loading, setLoading] = useState(!stateClassroom); // skip loading if we already have data
  const [error, setError] = useState('');
  const [tab, setTab] = useState<Tab>('overview');
  const [showBroadcast, setShowBroadcast] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  useEffect(() => {
    if (!id) return;
    // Always fetch fresh data. If the backend returns my_role in the detail
    // endpoint, great. If not, preserve the my_role we already have from the
    // list page so identity determination is never broken.
    getClassroom(id)
      .then(fresh => {
        setClassroom(prev => ({
          ...fresh,
          // my_role may be absent in the detail response — keep the known value
          my_role: fresh.my_role ?? prev?.my_role ?? 'student',
        }));
      })
      .catch(err => {
        // If we already have stale data, don't wipe it — just show no error
        if (!stateClassroom) setError(err?.message || 'Classroom not found.');
      })
      .finally(() => setLoading(false));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const isTeacher = classroom?.my_role === 'owner' || classroom?.my_role === 'teacher';
  const isOwner = classroom?.my_role === 'owner';

  async function handleArchive() {
    if (!classroom || !confirm(`Archive "${classroom.name}"? Members can still view it, but no new tasks can be posted.`)) return;
    try {
      if (classroom.archived_at) {
        await unarchiveClassroom(classroom.id);
      } else {
        await archiveClassroom(classroom.id);
      }
      setClassroom(prev => prev ? ({ ...prev, archived_at: prev.archived_at ? null : new Date().toISOString() }) : prev);
    } catch (err: any) {
      alert(err?.message || 'Failed to update archive status.');
    }
  }

  async function handleDelete() {
    if (!classroom || !confirm(`Permanently dissolve "${classroom.name}"? This cannot be undone.`)) return;
    try {
      await deleteClassroom(classroom.id);
      navigate('/classroom');
    } catch (err: any) {
      alert(err?.message || 'Failed to delete classroom.');
    }
  }

  async function handleLeave() {
    if (!classroom || !confirm(`Leave "${classroom.name}"?`)) return;
    try {
      await leaveClassroom(classroom.id);
      navigate('/classroom');
    } catch (err: any) {
      alert(err?.message || 'Failed to leave classroom.');
    }
  }

  // ─── Loading ───────────────────────────────────────────────────────────────

  if (loading) {
    return (
      <div className="cl-root cl-page">
        <div className="cl-page-inner">
          <div style={{ paddingTop: '2.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div className="cl-skeleton" style={{ height: 28, width: 200, borderRadius: 8 }} />
            <div className="cl-skeleton" style={{ height: 18, width: 140, borderRadius: 6 }} />
            <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
              {[...Array(3)].map((_, i) => <div key={i} className="cl-skeleton" style={{ height: 36, width: 90, borderRadius: 6 }} />)}
            </div>
            <div className="cl-skeleton" style={{ height: 1, borderRadius: 0, marginTop: 4 }} />
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginTop: 8 }}>
              {[...Array(4)].map((_, i) => <div key={i} className="cl-skeleton" style={{ height: 60, borderRadius: 10 }} />)}
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !classroom) {
    return (
      <div className="cl-root cl-page">
        <div className="cl-page-inner">
          <div className="cl-empty" style={{ marginTop: '3rem' }}>
            <p className="cl-empty__title">{error || 'Classroom not found'}</p>
            <Link to="/classroom" className="cl-btn cl-btn-secondary" style={{ marginTop: '0.5rem', textDecoration: 'none' }}>
              ← Back to Classrooms
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // ─── Tabs definition ───────────────────────────────────────────────────────

  const TABS: { key: Tab; label: string }[] = [
    { key: 'overview', label: 'Overview' },
    { key: 'assignments', label: 'Assignments' },
    { key: 'members', label: `Members (${classroom.member_count})` },
  ];

  return (
    <div className="cl-root cl-page">
      <div className="cl-page-inner">

        {/* Header */}
        <div className="cl-detail-header">
          <div className="cl-detail-title-wrap">
            <Link to="/classroom" className="cl-detail-back">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round"><polyline points="15 18 9 12 15 6"/></svg>
              Classrooms
            </Link>
            <h1 className="cl-detail-title">{classroom.name}</h1>
            <div className="cl-detail-meta">
              <RoleBadge role={classroom.my_role} />
              {classroom.archived_at && (
                <span className="cl-card__archived">Archived</span>
              )}
              <span style={{ fontSize: '0.78rem', color: 'var(--cl-text-muted)' }}>
                {classroom.member_count} member{classroom.member_count !== 1 ? 's' : ''}
              </span>
            </div>
          </div>

          {/* Actions */}
          <div className="cl-detail-actions">
            {/* Leave — available to teachers and students (not owner) */}
            {!isOwner && (
              <button className="cl-btn cl-btn-ghost cl-btn-sm" onClick={handleLeave} style={{ color: 'var(--cl-overdue)' }}>
                Leave Class
              </button>
            )}
            {isTeacher && (
              <button className="cl-btn cl-btn-secondary cl-btn-sm" onClick={() => setShowBroadcast(true)}>
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M3 11l18-5-5 18-5-8-8-5z"/>
                </svg>
                Announce
              </button>
            )}
            {isOwner && (
              <div style={{ position: 'relative' }}>
                <button
                  className="cl-btn-icon"
                  title="Settings"
                  onClick={() => setShowSettings(o => !o)}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                    <circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z"/>
                  </svg>
                </button>
                {showSettings && (
                  <SettingsDropdown
                    classroom={classroom}
                    onArchive={handleArchive}
                    onDelete={handleDelete}
                    onRename={async (name) => {
                      const updated = await renameClassroom(classroom.id, name);
                      setClassroom(updated);
                      setShowSettings(false);
                    }}
                    onClose={() => setShowSettings(false)}
                  />
                )}
              </div>
            )}
          </div>
        </div>

        {/* Tabs */}
        <div className="cl-tabs" role="tablist">
          {TABS.map(t => (
            <button
              key={t.key}
              role="tab"
              aria-selected={tab === t.key}
              className={`cl-tab${tab === t.key ? ' cl-tab--active' : ''}`}
              onClick={() => setTab(t.key)}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* Tab content */}
        <div role="tabpanel">
          {tab === 'overview' && (
            isTeacher
              ? <TeacherOverview classroom={classroom} onBroadcast={() => setShowBroadcast(true)} />
              : <StudentOverview classroom={classroom} />
          )}
          {tab === 'assignments' && <AssignmentsTab classroom={classroom} />}
          {tab === 'members' && <MembersTab classroom={classroom} />}
        </div>

      </div>

      {showBroadcast && (
        <BroadcastModal
          classroomId={classroom.id}
          classroomName={classroom.name}
          onClose={() => setShowBroadcast(false)}
        />
      )}
    </div>
  );
};

// ─── Settings dropdown ────────────────────────────────────────────────────────

interface SettingsDropdownProps {
  classroom: Classroom;
  onArchive: () => void;
  onDelete: () => void;
  onRename: (name: string) => Promise<void>;
  onClose: () => void;
}

const SettingsDropdown: React.FC<SettingsDropdownProps> = ({ classroom, onArchive, onDelete, onRename, onClose }) => {
  const [renaming, setRenaming] = useState(false);
  const [newName, setNewName] = useState(classroom.name);
  const [renameLoading, setRenameLoading] = useState(false);

  // Close on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      const target = e.target as Element;
      if (!target.closest('.cl-settings-dropdown')) onClose();
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [onClose]);

  return (
    <div
      className="cl-settings-dropdown"
      style={{
        position: 'absolute',
        right: 0,
        top: '110%',
        background: 'var(--cl-surface)',
        borderRadius: 'var(--cl-radius)',
        boxShadow: 'var(--cl-shadow-modal)',
        border: '1.5px solid var(--cl-border)',
        zIndex: 200,
        minWidth: 200,
        overflow: 'hidden',
        animation: 'cl-slide-up 0.15s ease',
      }}
    >
      {!renaming ? (
        <>
          <button
            className="cl-btn cl-btn-ghost"
            style={{ width: '100%', justifyContent: 'flex-start', borderRadius: 0, padding: '0.65rem 1rem' }}
            onClick={() => setRenaming(true)}
          >
            Rename
          </button>
          <button
            className="cl-btn cl-btn-ghost"
            style={{ width: '100%', justifyContent: 'flex-start', borderRadius: 0, padding: '0.65rem 1rem' }}
            onClick={() => { onArchive(); onClose(); }}
          >
            {classroom.archived_at ? 'Unarchive' : 'Archive'}
          </button>
          <hr style={{ border: 'none', borderTop: '1px solid var(--cl-border)', margin: 0 }} />
          <button
            className="cl-btn cl-btn-ghost"
            style={{ width: '100%', justifyContent: 'flex-start', borderRadius: 0, padding: '0.65rem 1rem', color: 'var(--cl-overdue)' }}
            onClick={() => { onDelete(); onClose(); }}
          >
            Dissolve Class
          </button>
        </>
      ) : (
        <div style={{ padding: '0.85rem 1rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <span className="cl-label">Rename classroom</span>
          <input
            className="cl-input"
            value={newName}
            onChange={e => setNewName(e.target.value)}
            autoFocus
            onKeyDown={async e => {
              if (e.key === 'Enter') {
                setRenameLoading(true);
                try { await onRename(newName.trim()); }
                finally { setRenameLoading(false); }
              }
              if (e.key === 'Escape') setRenaming(false);
            }}
          />
          <div style={{ display: 'flex', gap: '0.4rem', justifyContent: 'flex-end' }}>
            <button className="cl-btn cl-btn-ghost cl-btn-sm" onClick={() => setRenaming(false)}>Cancel</button>
            <button
              className="cl-btn cl-btn-primary cl-btn-sm"
              disabled={renameLoading || !newName.trim()}
              onClick={async () => {
                setRenameLoading(true);
                try { await onRename(newName.trim()); }
                finally { setRenameLoading(false); }
              }}
            >
              {renameLoading ? 'Saving…' : 'Save'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

