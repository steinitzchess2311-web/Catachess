import React, { useEffect, useState } from 'react';
import { listAssignments, getMyTodo, getChatGroupId } from '../api';
import type { Classroom, Assignment, TodoItem } from '../types';
import { CategoryBadge } from './CategoryBadge';
import { StatusBadge } from './StatusBadge';
import { formatDue, dueCssModifier } from '../utils';

const CATACHAT_URL = 'https://catachat.catachess.com';

function openCatachat(groupId: string) {
  const token = localStorage.getItem('catachess_token') || sessionStorage.getItem('catachess_token');
  const url = `${CATACHAT_URL}/group/${groupId}${token ? `?token=${encodeURIComponent(token)}` : ''}`;
  window.open(url, '_blank', 'noopener,noreferrer');
}

// ─── Teacher overview ─────────────────────────────────────────────────────────

interface TeacherOverviewProps {
  classroom: Classroom;
  onBroadcast: () => void;
}

export const TeacherOverview: React.FC<TeacherOverviewProps> = ({ classroom, onBroadcast }) => {
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listAssignments(classroom.id)
      .then(data => setAssignments(data.slice(0, 5)))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [classroom.id]);

  const totalTargets = assignments.reduce((s, a) => s + (a.member_count ?? 0), 0);
  const totalSubmitted = assignments.reduce((s, a) => s + (a.submission_count ?? 0), 0);

  return (
    <div>
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

      {/* Actions row */}
      <div style={{ display: 'flex', gap: '0.6rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
        <button className="cl-btn cl-btn-secondary" onClick={onBroadcast}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M3 11l18-5-5 18-5-8-8-5z"/>
          </svg>
          Broadcast
        </button>
        <button className="cl-btn cl-btn-secondary" onClick={async () => {
          try {
            const { catchat_group_id } = await getChatGroupId(classroom.id);
            if (catchat_group_id) openCatachat(catchat_group_id);
          } catch {}
        }}>
          Open Chat →
        </button>
      </div>

      {/* Recent assignments */}
      <div className="cl-section-header">
        <h3 className="cl-section-title">Recent Assignments</h3>
      </div>

      {loading ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {[...Array(3)].map((_, i) => (
            <div key={i} className="cl-skeleton" style={{ height: 52, borderRadius: 10 }} />
          ))}
        </div>
      ) : assignments.length === 0 ? (
        <div className="cl-empty">
          <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/></svg>
          <p className="cl-empty__title">No assignments yet</p>
          <p className="cl-empty__sub">Go to the Assignments tab to publish your first task.</p>
        </div>
      ) : (
        <div className="cl-asgn-list">
          {assignments.map(a => (
            <div key={a.id} className="cl-asgn-card">
              <div className="cl-asgn-card__left">
                <span className="cl-asgn-card__title">{a.title}</span>
                <div className="cl-asgn-card__sub">
                  <CategoryBadge category={a.category} />
                  {a.due_date && (
                    <span className={`cl-asgn-card__due cl-asgn-card__due--${dueCssModifier(a.due_date)}`}>
                      Due {formatDue(a.due_date)}
                    </span>
                  )}
                </div>
              </div>
              <div className="cl-asgn-card__right">
                <span className="cl-asgn-card__progress">
                  {a.submission_count ?? 0} / {a.member_count ?? '—'} submitted
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// ─── Student overview ─────────────────────────────────────────────────────────

interface StudentOverviewProps {
  classroom: Classroom;
}

export const StudentOverview: React.FC<StudentOverviewProps> = ({ classroom }) => {
  const [todo, setTodo] = useState<TodoItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getMyTodo()
      .then(all => setTodo(all.filter(t => !t.classroom_id || t.classroom_id === classroom.id || t.classroom_name === classroom.name)))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [classroom.id]);

  const overdueCount = todo.filter(t => t.urgency === 'overdue').length;
  const dueSoonCount = todo.filter(t => t.urgency === 'due_soon').length;

  return (
    <div>
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
          <span className="cl-ov-stat__val">{todo.filter(t => t.my_status === 'submitted').length}</span>
          <span className="cl-ov-stat__lbl">Completed</span>
        </div>
      </div>

      {/* Chat button */}
      <div style={{ marginBottom: '1.5rem' }}>
        <button className="cl-btn cl-btn-secondary" onClick={async () => {
          try {
            const { catchat_group_id } = await getChatGroupId(classroom.id);
            if (catchat_group_id) openCatachat(catchat_group_id);
          } catch {}
        }}>
          Open Class Chat →
        </button>
      </div>

      <div className="cl-section-header">
        <h3 className="cl-section-title">My Tasks</h3>
      </div>

      {loading ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {[...Array(3)].map((_, i) => (
            <div key={i} className="cl-skeleton" style={{ height: 52, borderRadius: 10 }} />
          ))}
        </div>
      ) : todo.length === 0 ? (
        <div className="cl-empty">
          <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
          <p className="cl-empty__title">All caught up!</p>
          <p className="cl-empty__sub">No pending tasks for this class.</p>
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
  );
};
