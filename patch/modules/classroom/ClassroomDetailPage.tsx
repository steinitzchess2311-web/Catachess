// ─── /classroom/:id ── Classroom detail ──────────────────────────────────────

import React, { useEffect, useState } from 'react';
import { Link, useParams, useNavigate, useLocation } from 'react-router-dom';
import { getClassroom, archiveClassroom, unarchiveClassroom, deleteClassroom, renameClassroom, leaveClassroom, listMembers, contactTeacher } from './api';
import type { Classroom } from './types';
import { RoleBadge } from './components/RoleBadge';
import { TeacherOverview, StudentOverview, openClassChat } from './components/overview';
import { MembersTab } from './components/MembersTab';
import { AssignmentsTab } from './components/AssignmentsTab';
import { BroadcastModal } from './components/BroadcastModal';
import { WorkspaceShareModal } from './components/WorkspaceShareModal';
import './classroom.css';

type Tab = 'overview' | 'assignments' | 'members';

export const ClassroomDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const location = useLocation();

  const stateClassroom = (location.state as { classroom?: Classroom } | null)?.classroom ?? null;

  const [classroom, setClassroom] = useState<Classroom | null>(stateClassroom);
  const [loading, setLoading] = useState(!stateClassroom);
  const [error, setError] = useState('');
  const [tab, setTab] = useState<Tab>('overview');
  const [showBroadcast, setShowBroadcast] = useState(false);
  const [showMore, setShowMore] = useState(false);
  const [broadcastRefreshKey, setBroadcastRefreshKey] = useState(0);
  const [createRequestToken, setCreateRequestToken] = useState(0);
  const [focusTasksSignal, setFocusTasksSignal] = useState(0);
  const [showContactMenu, setShowContactMenu] = useState(false);
  const [showShareModal, setShowShareModal] = useState(false);
  const [shareSuccessMsg, setShareSuccessMsg] = useState<string | null>(null);
  const [contactLoading, setContactLoading] = useState(false);

  useEffect(() => {
    if (!id) return;

    getClassroom(id)
      .then(fresh => {
        setClassroom(prev => ({
          ...fresh,
          my_role: fresh.my_role ?? prev?.my_role ?? 'student',
          member_count: fresh.member_count ?? prev?.member_count ?? 0,
        }));
      })
      .catch(err => {
        if (!stateClassroom) setError(err?.message || 'Classroom not found.');
      })
      .finally(() => setLoading(false));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  useEffect(() => {
    if (!classroom?.id) return;
    listMembers(classroom.id)
      .then(rows => {
        setClassroom(prev => (prev ? { ...prev, member_count: rows.length } : prev));
      })
      .catch(() => {});
  }, [classroom?.id]);

  const isTeacher = classroom?.my_role === 'owner' || classroom?.my_role === 'teacher';
  const isOwner = classroom?.my_role === 'owner';
  const memberCount = classroom?.member_count ?? 0;

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

  const TABS: { key: Tab; label: string }[] = [
    { key: 'overview', label: 'Overview' },
    { key: 'assignments', label: 'Assignments' },
    { key: 'members', label: `Members (${memberCount})` },
  ];

  return (
    <div className="cl-root cl-page">
      <div className="cl-page-inner">

        <div className="cl-detail-header">
          <div className="cl-detail-title-wrap">
            <Link to="/classroom" className="cl-detail-back">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round"><polyline points="15 18 9 12 15 6"/></svg>
              Classrooms
            </Link>
            <h1 className="cl-detail-title">{classroom.name}</h1>
            <div className="cl-detail-meta">
              <RoleBadge role={classroom.my_role} />
              {classroom.archived_at && <span className="cl-card__archived">Archived</span>}
              <span className="cl-detail-member-count">
                {memberCount} member{memberCount !== 1 ? 's' : ''}
              </span>
            </div>
          </div>

          <div className="cl-detail-actions">
            {isTeacher ? (
              <button
                className="cl-btn cl-btn-primary cl-btn-sm"
                onClick={() => {
                  setTab('assignments');
                  setCreateRequestToken(t => t + 1);
                }}
              >
                + Create Assignment
              </button>
            ) : (
              <div className="cl-more-wrap">
                <button
                  className="cl-btn cl-btn-primary cl-btn-sm"
                  onClick={() => setShowContactMenu(v => !v)}
                >
                  Contact Teacher
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="6 9 12 15 18 9"/>
                  </svg>
                </button>
                {showContactMenu && (
                  <ContactTeacherMenu
                    classroomId={classroom.id}
                    loading={contactLoading}
                    onMessage={async () => {
                      if (contactLoading) return;
                      setContactLoading(true);
                      try {
                        const res = await contactTeacher(classroom.id);
                        const token = localStorage.getItem('auth_token') || '';
                        window.open(
                          `https://catachat.catachess.com/${res.chat_type === 'conversation' ? 'conversation' : 'group'}/${res.chat_id}?token=${encodeURIComponent(token)}`,
                          '_blank',
                        );
                      } catch (err: any) {
                        alert(err?.message || 'Failed to open chat');
                      } finally {
                        setContactLoading(false);
                        setShowContactMenu(false);
                      }
                    }}
                    onShare={() => {
                      setShowShareModal(true);
                      setShowContactMenu(false);
                    }}
                    onClose={() => setShowContactMenu(false)}
                  />
                )}
              </div>
            )}

            {isTeacher && (
              <button className="cl-btn cl-btn-secondary cl-btn-sm" onClick={() => setShowBroadcast(true)}>
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M3 11l18-5-5 18-5-8-8-5z"/>
                </svg>
                Announce
              </button>
            )}

            <button className="cl-btn cl-btn-secondary cl-btn-sm" onClick={() => openClassChat(classroom.id)}>
              Open Class Chat →
            </button>

            <div className="cl-more-wrap">
              <button className="cl-btn cl-btn-ghost cl-btn-sm" onClick={() => setShowMore(v => !v)}>
                More
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="6 9 12 15 18 9"/>
                </svg>
              </button>
              {showMore && (
                <ClassroomMoreMenu
                  classroom={classroom}
                  isTeacher={isTeacher}
                  isOwner={isOwner}
                  onArchive={handleArchive}
                  onDelete={handleDelete}
                  onLeave={handleLeave}
                  onRename={async (name) => {
                    const updated = await renameClassroom(classroom.id, name);
                    setClassroom(prev => ({
                      ...updated,
                      my_role: updated.my_role ?? prev?.my_role ?? classroom.my_role,
                    }));
                    setShowMore(false);
                  }}
                  onClose={() => setShowMore(false)}
                />
              )}
            </div>
          </div>
        </div>

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

        <div role="tabpanel">
          {tab === 'overview' && (
            isTeacher
              ? <TeacherOverview classroom={classroom} broadcastRefreshKey={broadcastRefreshKey} />
              : <StudentOverview classroom={classroom} focusTasksSignal={focusTasksSignal} />
          )}
          {tab === 'assignments' && <AssignmentsTab classroom={classroom} createRequestToken={createRequestToken} />}
          {tab === 'members' && (
            <MembersTab
              classroom={classroom}
              onCountChange={(count) => {
                setClassroom(prev => (prev ? { ...prev, member_count: count } : prev));
              }}
            />
          )}
        </div>

      </div>

      {showBroadcast && (
        <BroadcastModal
          classroomId={classroom.id}
          classroomName={classroom.name}
          onClose={() => setShowBroadcast(false)}
          onSent={() => {
            setBroadcastRefreshKey(k => k + 1);
            setShowBroadcast(false);
          }}
        />
      )}

      {showShareModal && (
        <WorkspaceShareModal
          classroomId={classroom.id}
          onClose={() => setShowShareModal(false)}
          onShared={title => {
            setShowShareModal(false);
            setShareSuccessMsg(`"${title}" shared with teacher`);
            setTimeout(() => setShareSuccessMsg(null), 4000);
          }}
        />
      )}

      {shareSuccessMsg && (
        <div style={{ position: 'fixed', bottom: 24, left: '50%', transform: 'translateX(-50%)', background: 'var(--cl-bg-success, #d4edda)', color: 'var(--cl-text-success, #155724)', padding: '8px 18px', borderRadius: 8, fontSize: '0.85rem', zIndex: 1000 }}>
          {shareSuccessMsg}
        </div>
      )}
    </div>
  );
};

// ── Contact Teacher dropdown ──────────────────────────────────────────────────

interface ContactTeacherMenuProps {
  classroomId: string;
  loading: boolean;
  onMessage: () => void;
  onShare: () => void;
  onClose: () => void;
}

const ContactTeacherMenu: React.FC<ContactTeacherMenuProps> = ({ loading, onMessage, onShare, onClose }) => {
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      const target = e.target as Element;
      if (!target.closest('.cl-more-wrap')) onClose();
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [onClose]);

  return (
    <div className="cl-settings-dropdown">
      <button className="cl-menu-item" onClick={onMessage} disabled={loading}>
        {loading ? 'Opening…' : 'Message via CataChat'}
      </button>
      <button className="cl-menu-item" onClick={onShare}>
        Share Workspace
      </button>
    </div>
  );
};

// ── More menu ─────────────────────────────────────────────────────────────────

interface ClassroomMoreMenuProps {
  classroom: Classroom;
  isTeacher: boolean;
  isOwner: boolean;
  onArchive: () => void;
  onDelete: () => void;
  onLeave: () => void;
  onRename: (name: string) => Promise<void>;
  onClose: () => void;
}

const ClassroomMoreMenu: React.FC<ClassroomMoreMenuProps> = ({
  classroom,
  isTeacher,
  isOwner,
  onArchive,
  onDelete,
  onLeave,
  onRename,
  onClose,
}) => {
  const [renaming, setRenaming] = useState(false);
  const [newName, setNewName] = useState(classroom.name);
  const [renameLoading, setRenameLoading] = useState(false);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      const target = e.target as Element;
      if (!target.closest('.cl-more-wrap')) onClose();
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [onClose]);

  if (renaming) {
    return (
      <div className="cl-settings-dropdown">
        <div className="cl-menu-rename">
          <span className="cl-label">Rename classroom</span>
          <input
            className="cl-input"
            value={newName}
            onChange={e => setNewName(e.target.value)}
            autoFocus
            onKeyDown={async e => {
              if (e.key === 'Enter') {
                setRenameLoading(true);
                try {
                  await onRename(newName.trim());
                } finally {
                  setRenameLoading(false);
                }
              }
              if (e.key === 'Escape') setRenaming(false);
            }}
          />
          <div className="cl-menu-rename-actions">
            <button className="cl-btn cl-btn-ghost cl-btn-sm" onClick={() => setRenaming(false)}>Cancel</button>
            <button
              className="cl-btn cl-btn-primary cl-btn-sm"
              disabled={renameLoading || !newName.trim()}
              onClick={async () => {
                setRenameLoading(true);
                try {
                  await onRename(newName.trim());
                } finally {
                  setRenameLoading(false);
                }
              }}
            >
              {renameLoading ? 'Saving…' : 'Save'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="cl-settings-dropdown">
      {isTeacher && classroom.workspace_folder_id && (
        <a
          href={`/workspace?folder=${classroom.workspace_folder_id}`}
          target="_blank"
          rel="noreferrer"
          className="cl-menu-link"
        >
          Student Folders
        </a>
      )}

      {isOwner && (
        <>
          <button className="cl-menu-item" onClick={() => setRenaming(true)}>Rename Classroom</button>
          <button className="cl-menu-item" onClick={() => { onArchive(); onClose(); }}>
            {classroom.archived_at ? 'Unarchive' : 'Archive'}
          </button>
        </>
      )}

      {!isOwner && (
        <button className="cl-menu-item cl-menu-item--danger" onClick={() => { onLeave(); onClose(); }}>
          Leave Class
        </button>
      )}

      {isOwner && (
        <>
          <hr className="cl-menu-divider" />
          <button className="cl-menu-item cl-menu-item--danger" onClick={() => { onDelete(); onClose(); }}>
            Dissolve Class
          </button>
        </>
      )}
    </div>
  );
};
