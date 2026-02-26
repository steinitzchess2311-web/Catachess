// ─── OverviewTab — teacher & student views ────────────────────────────────────

import React, { useEffect, useState } from 'react';
import { listAssignments, getMyTodo, getChatGroupId } from '../api';
import type { Classroom, Assignment, TodoItem } from '../types';
import { CategoryBadge } from './CategoryBadge';
import { StatusBadge } from './StatusBadge';
import { ActivityFeed } from './ActivityFeed';
import { BroadcastBanner } from './BroadcastBanner';
import { BroadcastPanel } from './BroadcastPanel';
import { formatDue, dueCssModifier } from '../utils';

const CATACHAT_URL = 'https://catachat.catachess.com';

function openCatachat(classroomId: string) {
  getChatGroupId(classroomId)
    .then(({ catchat_group_id }) => {
      if (!catchat_group_id) return;
      const token = localStorage.getItem('catachess_token') || sessionStorage.getItem('catachess_token');
      const url = `${CATACHAT_URL}/group/${catchat_group_id}${token ? `?token=${encodeURIComponent(token)}` : ''}`;
      window.open(url, '_blank', 'noopener,noreferrer');
    })
    .catch(() => {});
}

// ─── Teacher Overview ─────────────────────────────────────────────────────────

interface TeacherOverviewProps {
  classroom: Classroom;
  onBroadcast: () => void;
  broadcastRefreshKey?: number;
}

export const TeacherOverview: React.FC<TeacherOverviewProps> = ({ classroom, onBroadcast, broadcastRefreshKey }) => {
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listAssignments(classroom.id)
      .then(data => setAssignments(data.slice(0, 5)))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [classroom.id]);

  const totalSubmitted = assignments.reduce((s, a) => s + (a.submission_count ?? 0), 0);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>

      {/* Quick stats */}
      <div className="cl-overview-stats">
        <div className="cl-ov-stat cl-ov-stat--accent">
          <span className="cl-ov-stat__val">{classroom.member_count}</span>
          <span className="cl-ov-stat__lbl">Members</span>
        </div>
        <div className="cl-ov-stat cl-ov-stat--green">
          <span className="cl-ov-stat__val">{assignments.length}</span>
          <span className="cl-ov-stat__lbl">Assignments</span>
        </div>
        <div className="cl-ov-stat cl-ov-stat--yellow">
          <span className="cl-ov-stat__val">{totalSubmitted}</span>
          <span className="cl-ov-stat__lbl">Submissions</span>
        </div>
      </div>

      {/* Action buttons */}
      <div style={{ display: 'flex', gap: '0.6rem', flexWrap: 'wrap' }}>
        <button className="cl-btn cl-btn-secondary" onClick={onBroadcast}>
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M3 11l18-5-5 18-5-8-8-5z"/>
          </svg>
          Broadcast Announcement
        </button>
        <button className="cl-btn cl-btn-secondary" onClick={() => openCatachat(classroom.id)}>
          Open Class Chat →
        </button>
      </div>

      {/* Three-column layout: Recent assignments + Announcements + Activity feed */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1.5rem', alignItems: 'start' }}>

        {/* Recent assignments */}
        <div>
          <div className="cl-section-header" style={{ marginBottom: '0.75rem' }}>
            <h3 className="cl-section-title">Recent Assignments</h3>
          </div>
          {loading ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {[...Array(3)].map((_, i) => <div key={i} className="cl-skeleton" style={{ height: 52, borderRadius: 8 }} />)}
            </div>
          ) : assignments.length === 0 ? (
            <p style={{ fontSize: '0.85rem', color: 'var(--cl-text-secondary)', margin: 0 }}>
              No assignments published yet.
            </p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {assignments.map(a => (
                <div key={a.id} style={{
                  background: 'var(--cl-surface)',
                  border: '1.5px solid var(--cl-border)',
                  borderRadius: 8,
                  padding: '0.7rem 0.9rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 4,
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <CategoryBadge category={a.category} />
                    <span style={{ fontSize: '0.85rem', fontWeight: 600, flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {a.title}
                    </span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '0.76rem', color: 'var(--cl-text-muted)' }}>
                      {a.due_date ? `Due ${formatDue(a.due_date)}` : 'No due date'}
                    </span>
                    <span style={{ fontSize: '0.76rem', color: 'var(--cl-text-secondary)', fontWeight: 500 }}>
                      {a.submission_count ?? 0}/{a.member_count ?? '—'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Announcements */}
        <BroadcastPanel classroomId={classroom.id} refreshKey={broadcastRefreshKey} />

        {/* Activity feed */}
        <div>
          <div className="cl-section-header" style={{ marginBottom: '0.75rem' }}>
            <h3 className="cl-section-title">Recent Activity</h3>
          </div>
          <ActivityFeed classroomId={classroom.id} />
        </div>
      </div>
    </div>
  );
};

// ─── Student Overview ─────────────────────────────────────────────────────────

interface StudentOverviewProps {
  classroom: Classroom;
}

export const StudentOverview: React.FC<StudentOverviewProps> = ({ classroom }) => {
  const [todo, setTodo]     = useState<TodoItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getMyTodo()
      .then(all =>
        setTodo(
          all.filter(t =>
            !t.classroom_id
              ? t.classroom_name === classroom.name
              : t.classroom_id === classroom.id,
          ),
        ),
      )
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [classroom.id, classroom.name]);

  const overdueCount  = todo.filter(t => t.urgency === 'overdue').length;
  const dueSoonCount  = todo.filter(t => t.urgency === 'due_soon').length;
  const doneCount     = todo.filter(t => t.my_status === 'submitted').length;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>

      {/* Broadcast announcements — prominently at top */}
      <BroadcastBanner classroomId={classroom.id} />

      {/* Quick stats */}
      <div className="cl-overview-stats">
        <div className={`cl-ov-stat ${overdueCount > 0 ? 'cl-ov-stat--red' : 'cl-ov-stat--green'}`}>
          <span className="cl-ov-stat__val">{overdueCount}</span>
          <span className="cl-ov-stat__lbl">Overdue</span>
        </div>
        <div className={`cl-ov-stat ${dueSoonCount > 0 ? 'cl-ov-stat--yellow' : 'cl-ov-stat--green'}`}>
          <span className="cl-ov-stat__val">{dueSoonCount}</span>
          <span className="cl-ov-stat__lbl">Due Soon</span>
        </div>
        <div className="cl-ov-stat cl-ov-stat--accent">
          <span className="cl-ov-stat__val">{doneCount}</span>
          <span className="cl-ov-stat__lbl">Completed</span>
        </div>
      </div>

      {/* Class chat button */}
      <div>
        <button className="cl-btn cl-btn-secondary" onClick={() => openCatachat(classroom.id)}>
          Open Class Chat →
        </button>
      </div>

      {/* Todo list */}
      <div>
        <div className="cl-section-header" style={{ marginBottom: '0.75rem' }}>
          <h3 className="cl-section-title">My Tasks</h3>
        </div>

        {loading ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {[...Array(3)].map((_, i) => <div key={i} className="cl-skeleton" style={{ height: 56, borderRadius: 10 }} />)}
          </div>
        ) : todo.length === 0 ? (
          <div className="cl-empty">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            <p className="cl-empty__title">All caught up!</p>
            <p className="cl-empty__sub">No pending tasks in this class.</p>
          </div>
        ) : (
          <div className="cl-todo-list">
            {todo.map(item => (
              <div key={item.assignment_id} className={`cl-todo-item cl-todo-item--${item.urgency}`}>
                <div className={`cl-urgency-dot cl-urgency-dot--${item.urgency}`} />
                <div className="cl-todo-item__body">
                  <p className="cl-todo-item__title">{item.title}</p>
                  <p className="cl-todo-item__sub">
                    {item.due_date ? `Due ${formatDue(item.due_date)}` : 'No due date'}
                  </p>
                </div>
                <StatusBadge status={item.my_status as any} />
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
