// ─── AssignmentsTab ───────────────────────────────────────────────────────────

import React, { useEffect, useState } from 'react';
import { listAssignments, deleteAssignment } from '../api';
import type { Classroom, Assignment, AssignmentCategory } from '../types';
import { CategoryBadge } from './CategoryBadge';
import { StatusBadge } from './StatusBadge';
import { CreateAssignmentModal } from './CreateAssignmentModal';
import { EditAssignmentModal } from './EditAssignmentModal';
import { StatsModal } from './StatsModal';
import { AssignmentDetailModal } from './AssignmentDetailModal';
import { formatDue, dueCssModifier } from '../utils';

const CATEGORY_FILTERS: { label: string; value: AssignmentCategory | 'all' }[] = [
  { label: 'All',        value: 'all'        },
  { label: 'Material',   value: 'material'   },
  { label: 'Assignment', value: 'assignment' },
  { label: 'Exam',       value: 'exam'       },
];

interface Props {
  classroom: Classroom;
  createRequestToken?: number;
}

export const AssignmentsTab: React.FC<Props> = ({ classroom, createRequestToken = 0 }) => {
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [loading, setLoading]         = useState(true);
  const [filter, setFilter]           = useState<AssignmentCategory | 'all'>('all');

  // Modals
  const [showCreate, setShowCreate]           = useState(false);
  const [statsTarget, setStatsTarget]         = useState<Assignment | null>(null);
  const [editTarget, setEditTarget]           = useState<Assignment | null>(null);
  const [detailTarget, setDetailTarget]       = useState<Assignment | null>(null);

  const isTeacher = classroom.my_role === 'owner' || classroom.my_role === 'teacher';

  useEffect(() => {
    setLoading(true);
    const params = filter !== 'all' ? { category: filter } : undefined;
    listAssignments(classroom.id, params)
      .then(setAssignments)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [classroom.id, filter]);

  useEffect(() => {
    if (!createRequestToken) return;
    setShowCreate(true);
  }, [createRequestToken]);

  async function handleDelete(id: string, title: string) {
    if (!confirm(`Retract "${title}"? This cannot be undone.`)) return;
    try {
      await deleteAssignment(classroom.id, id);
      setAssignments(prev => prev.filter(a => a.id !== id));
    } catch (err: any) {
      alert(err?.message || 'Failed to retract assignment.');
    }
  }

  return (
    <div>
      {/* Toolbar */}
      <div className="cl-section-header" style={{ marginBottom: '1rem', flexWrap: 'wrap', gap: '0.5rem' }}>
        <div style={{ display: 'flex', gap: '0.35rem', flexWrap: 'wrap' }}>
          {CATEGORY_FILTERS.map(f => (
            <button
              key={f.value}
              className={`cl-btn cl-btn-sm ${filter === f.value ? 'cl-btn-primary' : 'cl-btn-secondary'}`}
              onClick={() => setFilter(f.value)}
            >
              {f.label}
            </button>
          ))}
        </div>
        {isTeacher && (
          <button className="cl-btn cl-btn-primary cl-btn-sm" onClick={() => setShowCreate(true)}>
            + New Assignment
          </button>
        )}
      </div>

      {/* List */}
      {loading ? (
        <div className="cl-asgn-list">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="cl-skeleton" style={{ height: 68, borderRadius: 10 }} />
          ))}
        </div>
      ) : assignments.length === 0 ? (
        <div className="cl-empty">
          <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
          </svg>
          <p className="cl-empty__title">No assignments yet</p>
          {isTeacher && (
            <p className="cl-empty__sub">Click "+ New Assignment" to publish a task for your students.</p>
          )}
        </div>
      ) : (
        <div className="cl-asgn-list">
          {assignments.map(a => (
            <AssignmentRow
              key={a.id}
              assignment={a}
              isTeacher={isTeacher}
              onOpen={() => isTeacher ? setStatsTarget(a) : setDetailTarget(a)}
              onEdit={() => setEditTarget(a)}
              onDelete={() => handleDelete(a.id, a.title)}
            />
          ))}
        </div>
      )}

      {/* ── Modals ── */}

      {showCreate && (
        <CreateAssignmentModal
          classroomId={classroom.id}
          onClose={() => setShowCreate(false)}
          onCreated={a => {
            setAssignments(prev => [a, ...prev]);
            setShowCreate(false);
          }}
        />
      )}

      {editTarget && (
        <EditAssignmentModal
          classroomId={classroom.id}
          assignment={editTarget}
          onClose={() => setEditTarget(null)}
          onUpdated={updated => {
            setAssignments(prev => prev.map(a => a.id === updated.id ? updated : a));
            setEditTarget(null);
          }}
        />
      )}

      {statsTarget && (
        <StatsModal
          classroomId={classroom.id}
          assignment={statsTarget}
          onClose={() => setStatsTarget(null)}
        />
      )}

      {detailTarget && (
        <AssignmentDetailModal
          classroomId={classroom.id}
          assignment={detailTarget}
          onClose={() => setDetailTarget(null)}
          onSubmitted={() => {
            // Refresh list to update submission status
            listAssignments(classroom.id, filter !== 'all' ? { category: filter } : undefined)
              .then(setAssignments)
              .catch(() => {});
            setDetailTarget(null);
          }}
        />
      )}
    </div>
  );
};

// ─── Assignment row ───────────────────────────────────────────────────────────

interface RowProps {
  assignment: Assignment;
  isTeacher: boolean;
  onOpen: () => void;
  onEdit: () => void;
  onDelete: () => void;
}

const AssignmentRow: React.FC<RowProps> = ({ assignment: a, isTeacher, onOpen, onEdit, onDelete }) => {
  const dueModifier = a.due_date ? dueCssModifier(a.due_date) : 'normal';
  const isOverdue   = a.due_date ? new Date(a.due_date) < new Date() : false;

  return (
    <div
      className="cl-asgn-card"
      onClick={onOpen}
      style={{ cursor: 'pointer' }}
      role="button"
      tabIndex={0}
      onKeyDown={e => e.key === 'Enter' && onOpen()}
    >
      {/* Left */}
      <div className="cl-asgn-card__left">
        <span className="cl-asgn-card__title">{a.title}</span>
        <div className="cl-asgn-card__sub">
          <CategoryBadge category={a.category} />
          <span style={{ fontSize: '0.76rem', color: 'var(--cl-text-muted)', textTransform: 'capitalize' }}>
            {a.type}
          </span>
          {a.due_date ? (
            <span className={`cl-asgn-card__due cl-asgn-card__due--${dueModifier}`}>
              {isOverdue ? 'Was due' : 'Due'} {formatDue(a.due_date)}
            </span>
          ) : (
            <span style={{ fontSize: '0.76rem', color: 'var(--cl-text-muted)' }}>No due date</span>
          )}
        </div>
      </div>

      {/* Right */}
      <div className="cl-asgn-card__right" onClick={e => e.stopPropagation()}>
        {/* Teacher: submission count + action icons */}
        {isTeacher && (
          <>
            {a.submission_count !== undefined && (
              <span className="cl-asgn-card__progress" style={{ fontSize: '0.82rem' }}>
                {a.submission_count} / {a.member_count ?? '—'} submitted
              </span>
            )}
            {/* Stats */}
            <button
              className="cl-btn-icon"
              title="View stats"
              onClick={e => { e.stopPropagation(); onOpen(); }}
            >
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <line x1="18" y1="20" x2="18" y2="10"/>
                <line x1="12" y1="20" x2="12" y2="4"/>
                <line x1="6"  y1="20" x2="6"  y2="14"/>
              </svg>
            </button>
            {/* Edit */}
            <button
              className="cl-btn-icon"
              title="Edit assignment"
              onClick={e => { e.stopPropagation(); onEdit(); }}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
                <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
              </svg>
            </button>
            {/* Delete */}
            <button
              className="cl-btn-icon"
              title="Retract"
              onClick={e => { e.stopPropagation(); onDelete(); }}
              style={{ color: 'var(--cl-text-muted)' }}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <polyline points="3 6 5 6 21 6"/>
                <path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6"/>
                <path d="M10 11v6M14 11v6"/>
              </svg>
            </button>
          </>
        )}

        {/* Student: submission status + open button */}
        {!isTeacher && (
          <>
            {a.my_submission ? (
              <StatusBadge status={a.my_submission.status} />
            ) : (
              <span className="cl-status-badge cl-status-badge--not_started">Not Started</span>
            )}
            {a.category !== 'material' && (
              <button
                className="cl-btn cl-btn-primary cl-btn-sm"
                onClick={e => { e.stopPropagation(); onOpen(); }}
                style={{ flexShrink: 0 }}
              >
                {a.my_submission?.status === 'submitted' ? 'View' : 'Open'}
              </button>
            )}
          </>
        )}
      </div>
    </div>
  );
};
